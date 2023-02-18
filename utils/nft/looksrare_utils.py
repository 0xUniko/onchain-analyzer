from utils.nft.nft_transactions_analysis import weth
from utils.nft.seaport_utils import DealBalance
from utils.Scanner import w3
from hexbytes import HexBytes
from eth_typing.evm import HexAddress, ChecksumAddress
from enum import IntEnum
import json
from typing import cast, TypedDict

looksrare_addr = cast(ChecksumAddress, "0x59728544B08AB483533076417FbBB2fD0B17CE3a")

with open("utils/looksrare_abi.json", "r") as f:
    looksrare_abi = json.load(f)
looksrare_contract = w3.eth.contract(address=looksrare_addr, abi=looksrare_abi)


class TakerType(IntEnum):
    taker_bid = 1
    taker_ask = -1


class TakerEvent(TypedDict):
    taker: ChecksumAddress
    maker: ChecksumAddress
    strategy: ChecksumAddress
    orderHash: HexBytes
    orderNonce: int
    currency: ChecksumAddress
    collection: ChecksumAddress
    tokenId: int
    amount: int
    price: int


class LoyaltyPaymentDict(TypedDict):
    collection: ChecksumAddress
    tokenId: int
    royaltyRecipient: ChecksumAddress
    currency: ChecksumAddress
    amount: int


def get_taker_balance(
    account: HexAddress,
    taker: TakerEvent,
    loyalty: LoyaltyPaymentDict | None,
    taker_type: TakerType,
) -> DealBalance:
    assert (
        taker["collection"] == loyalty["collection"]
        and taker["tokenId"] == loyalty["tokenId"]
        if loyalty is not None
        else True
    ), "Taker event and LoyaltyPayment event does not match"

    if (
        taker_type == TakerType.taker_bid and taker["maker"].lower() != account.lower()
    ) or (
        taker_type == TakerType.taker_ask and taker["maker"].lower() == account.lower
    ):
        eth = -taker["amount"] / 10**18
    else:
        assert (
            loyalty["currency"] == weth if loyalty is not None else True
        ), "loyalty not paid in weth"

        eth = (
            taker["amount"] - loyalty["amount"] if loyalty is not None else 0
        ) / 10**18

    return {
        "eth": eth,
        "nft_address": taker["collection"],
        "nft_amount": taker["amount"],
    }
