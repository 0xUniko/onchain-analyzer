from utils.Scanner import w3
from utils.CompleteGetter import CompleteGetter
from utils.nft.seaport_utils import OrderFulfilled_event_sig, OrderFulfilledEvent
from utils.nft.x2y2_utils import (
    EvInventoryEvent,
    EvProfitDict,
    x2y2_contract,
    get_x2y2_tx_balance,
)
from hexbytes import HexBytes
from eth_typing.evm import HexAddress, Address, ChecksumAddress
from web3.types import TxReceipt
from web3._utils.events import EventLogErrorFlags
import pandas as pd
import datetime, time
from tqdm import tqdm
from tenacity import retry
from tenacity.wait import wait_random
from tenacity.stop import stop_after_attempt
from typing import cast, List

weth = cast(ChecksumAddress, "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
from utils.nft.looksrare_utils import (
    LoyaltyPaymentDict,
    get_taker_balance,
    TakerType,
    looksrare_contract,
    TakerEvent,
)


def get_OrderFulfilled_balance(account: HexAddress, receipt: TxReceipt):
    OrderFulfilled_events = [
        OrderFulfilledEvent(log["topics"], log["data"])
        for log in receipt["logs"]
        if log["topics"][0] == OrderFulfilled_event_sig
    ]

    return pd.DataFrame(
        [
            b.get_deal_balance(account)
            for b in OrderFulfilled_events
            if (b.offerer == account or b.recipient == account)
            and b.consideration_length > 0
            # one event in 0xb93ee1dfc1f448e28188a447cbfcbe23886b0f32cf5fa6f20a7a69c20a10e782 is strange
        ]
    )


def add_nftname_time_hash_and_merge(df: pd.DataFrame, transfers: pd.DataFrame):
    if df.empty:
        return df
    else:
        df["nft_address"] = df["nft_address"].map(lambda x: x.lower())

        df = df.groupby("nft_address").sum().reset_index()

        df = pd.merge(
            df,
            transfers.rename(
                columns={"contractAddress": "nft_address", "tokenName": "nft_name"}
            )[["nft_address", "nft_name"]],
            how="left",
            on="nft_address",
        ).drop_duplicates()

        assert (
            (df["nft_name"].notnull()) | (df["eth"] < 0)
        ).all(), "not all names are assigned"

        df["time"] = datetime.datetime.fromtimestamp(
            int(transfers["timeStamp"].iloc[0])
        ).strftime("%Y-%m-%d %H:%M:%S")

        df["tx_hash"] = transfers["hash"].iloc[0]

        return df[["eth", "nft_amount", "nft_name", "time", "tx_hash"]]


def get_EvInventory_balance(
    account: HexAddress, receipt: TxReceipt, transfers: pd.DataFrame
):
    ev_inventory_events = [
        EvInventoryEvent(r["args"])
        for r in x2y2_contract.events.EvInventory().processReceipt(
            receipt, errors=EventLogErrorFlags.Discard
        )
    ]

    ev_profit_events = x2y2_contract.events.EvProfit().processReceipt(
        receipt, errors=EventLogErrorFlags.Discard
    )

    assert len(ev_profit_events) == len(
        ev_inventory_events
    ), "ev_profit_events do not match with ev_inventory_events"

    def find_the_corresponding_profit_event(itemHash: HexBytes) -> EvProfitDict:
        corresponding_profit_events = [
            r["args"] for r in ev_profit_events if r["args"]["itemHash"] == itemHash
        ]

        assert (
            len(corresponding_profit_events) == 1
        ), "found multiple corresponding events"

        return corresponding_profit_events[0]

    return pd.DataFrame(
        [
            get_x2y2_tx_balance(
                b, find_the_corresponding_profit_event(b.detail["itemHash"]), account
            )
            for b in ev_inventory_events
            if any(
                (transfers["contractAddress"] == b.item["data"]["token"])
                & (transfers["tokenID"].map(int) == b.item["data"]["identifier"])
            )
        ]
    )


def get_TakerBid_TakerAsk_balance(
    account: HexAddress, receipt: TxReceipt, transfers: pd.DataFrame
):
    taker_ask = looksrare_contract.events.TakerAsk().processReceipt(
        receipt, errors=EventLogErrorFlags.Discard
    )
    taker_bid = looksrare_contract.events.TakerBid().processReceipt(
        receipt, errors=EventLogErrorFlags.Discard
    )
    royalty_payment = looksrare_contract.events.RoyaltyPayment().processReceipt(
        receipt, errors=EventLogErrorFlags.Discard
    )

    assert not (
        taker_bid != () and taker_ask != ()
    ), "both TakerAsk and TakerBid event are non-empty"

    assert all(
        [b["args"]["currency"] == weth for b in royalty_payment]
    ), "royalty not paid in eth"

    def find_the_corresponding_royalty_payment(
        collection: ChecksumAddress, tokenId: int
    ) -> LoyaltyPaymentDict | None:
        if royalty_payment == ():
            return None

        corresponding_payments = [
            pay["args"]
            for pay in royalty_payment
            if pay["args"]["collection"] == collection
            and pay["args"]["tokenId"] == tokenId
        ]

        assert len(corresponding_payments) <= 1, "found multiple corresponding payments"

        if len(corresponding_payments) == 1:
            return corresponding_payments[0]
        else:
            return None

    if taker_bid != ():
        taker: List[TakerEvent] = [t["args"] for t in taker_bid]
        taker_type = TakerType.taker_bid
    else:
        taker: List[TakerEvent] = [t["args"] for t in taker_ask]
        taker_type = TakerType.taker_ask

    return pd.DataFrame(
        [
            get_taker_balance(
                account,
                t,
                find_the_corresponding_royalty_payment(t["collection"], t["tokenId"]),
                taker_type,
            )
            for t in taker
            if any(
                (transfers["contractAddress"] == t["collection"].lower())
                & (transfers["tokenID"].astype(int) == t["tokenId"])
            )
        ]
    )


@retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=1.5), reraise=True)
def account_nft_transactions(
    account: HexAddress | Address, start_time: int | None = None
):
    if isinstance(account, bytes):
        account = cast(HexAddress, account.hex().lower())
    else:
        account = cast(HexAddress, account.lower())

    result = pd.DataFrame([])
    for _ in range(3):
        with CompleteGetter() as getter:
            nft_transfers = getter.get_all(account, "tokennfttx", start_time)

        if nft_transfers.empty:
            time.sleep(1.5)
            continue
        else:
            nft_transfers_in_30days = nft_transfers.loc[
                nft_transfers["timeStamp"].map(
                    lambda x: datetime.date.fromtimestamp(int(x))
                    > datetime.date.today() - datetime.timedelta(days=30)
                )
            ]

            print("get account nft balances")
            balances = []
            for hash in tqdm(nft_transfers_in_30days["hash"].drop_duplicates()):
                receipt = w3.eth.get_transaction_receipt(hash)

                transfers = nft_transfers_in_30days.loc[
                    nft_transfers_in_30days["hash"] == hash
                ]

                new_balances = []

                new_balances.append(get_OrderFulfilled_balance(account, receipt))

                new_balances.append(
                    get_EvInventory_balance(account, receipt, transfers)
                )

                new_balances.append(
                    get_TakerBid_TakerAsk_balance(account, receipt, transfers)
                )

                balances.extend(
                    [
                        add_nftname_time_hash_and_merge(b, transfers)
                        for b in new_balances
                    ]
                )

        result = pd.concat(balances, ignore_index=True)
        break
    return result
