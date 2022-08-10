from utils.Scanner import w3
from utils.CompleteGetter import CompleteGetter
from utils.seaport_utils import OrderFulfilled_event_sig, OrderFulfilledEvent
from utils.x2y2_utils import EvInventoryEvent, EvProfitDict, x2y2_contract, get_x2y2_tx_balance
from hexbytes import HexBytes
from eth_typing.evm import HexAddress, Address
from web3.types import TxReceipt
import pandas as pd
import datetime, time
from tqdm import tqdm
from tenacity import retry
from tenacity.wait import wait_random
from tenacity.stop import stop_after_attempt
from typing import cast


def get_OrderFulfilled_balance(account: HexAddress, receipt: TxReceipt):
    OrderFulfilled_events = [
        OrderFulfilledEvent(log['topics'], log['data'])
        for log in receipt['logs']
        if log['topics'][0] == OrderFulfilled_event_sig
    ]

    return pd.DataFrame([
        b.get_deal_balance(account) for b in OrderFulfilled_events
        if b.offerer == account or b.recipient == account
    ])


def get_EvInventory_balance(account: HexAddress, receipt: TxReceipt,
                            tokenIds: set[int]):
    ev_inventory_events = [
        EvInventoryEvent(r['args'])
        for r in x2y2_contract.events.EvInventory().processReceipt(receipt)
    ]

    ev_profit_events = x2y2_contract.events.EvProfit().processReceipt(receipt)

    assert len(ev_profit_events) == len(
        ev_inventory_events
    ), 'ev_profit_events do not match with ev_inventory_events'

    assert pd.Series([
        t.item['data']['token'] for t in ev_inventory_events
    ]).nunique() == 1, 'more than one nft collections are traded in this tx'

    def find_the_corresponding_profit_event(
            itemHash: HexBytes) -> EvProfitDict:
        corresponding_profit_events = [
            r['args'] for r in ev_profit_events
            if r['args']['itemHash'] == itemHash
        ]

        assert len(corresponding_profit_events
                   ) == 1, 'found multiple corresponding events'

        return corresponding_profit_events[0]

    return pd.DataFrame([
        get_x2y2_tx_balance(
            b, find_the_corresponding_profit_event(b.detail['itemHash']),
            account) for b in ev_inventory_events
        if b.item['data']['identifier'] in tokenIds
    ])


# def get_TakerBid_TakerAsk_balance(account: HexAddress, receipt: TxReceipt,
#                                   hash: HexStr, token_name: str,
#                                   timeStamp: int):
#     pass


def add_nftname_time_hash(df: pd.DataFrame, token_name: str, timeStamp: int,
                          hash: HexBytes):
    df['nft_name'] = token_name
    df['time'] = datetime.datetime.fromtimestamp(timeStamp).strftime(
        '%Y-%m-%d %H:%M:%S')
    df['tx_hash'] = hash
    return df


@retry(stop=stop_after_attempt(3),
       wait=wait_random(min=1, max=1.5),
       reraise=True)
def account_nft_transactions(account: HexAddress | Address):
    if isinstance(account, bytes):
        account = cast(HexAddress, account.hex().lower())
    else:
        account = cast(HexAddress, account.lower())

    result = pd.DataFrame([])
    for _ in range(3):
        with CompleteGetter() as getter:
            nft_transfers = getter.get_all(account, 'tokennfttx')

        if nft_transfers.empty:
            time.sleep(1.5)
            continue
        else:
            nft_transfers_in_30days = nft_transfers.loc[nft_transfers[
                'timeStamp'].map(lambda x: datetime.date.fromtimestamp(int(
                    x)) > datetime.date.today() - datetime.timedelta(days=30))]

            print('get account nft balances')
            balances = []
            for hash in tqdm(
                    nft_transfers_in_30days['hash'].drop_duplicates()):

                receipt = w3.eth.get_transaction_receipt(hash)

                transfers = nft_transfers_in_30days.loc[
                    nft_transfers_in_30days['hash'] == hash]

                tokenIds = set(transfers['tokenID'])

                tokenName, timeStamp = transfers.iloc[0][[
                    'tokenName', 'timeStamp'
                ]]

                balances_length = len(balances)

                balances.append(
                    add_nftname_time_hash(
                        get_OrderFulfilled_balance(account, receipt),
                        tokenName, int(timeStamp), receipt['transactionHash']))

                balances.append(
                    add_nftname_time_hash(
                        get_EvInventory_balance(account, receipt, tokenIds),
                        tokenName, int(timeStamp), receipt['transactionHash']))

                tokenName_length = cast(
                    pd.DataFrame, nft_transfers_in_30days.loc[
                        nft_transfers_in_30days['hash'] == hash,
                        'tokenName']).nunique()

                assert (
                    tokenName_length > 1 and balances_length == len(balances)
                ) or tokenName_length == 1, 'more than one nft collection is traded'

        result = pd.concat(balances, ignore_index=True)
        break
    return result