from utils.Scanner import w3
from utils.seaport_utils import DealBalance
from eth_typing.evm import ChecksumAddress, HexAddress
from hexbytes import HexBytes
import json
from enum import IntEnum
from typing import List, Tuple, cast, TypedDict

x2y2_addr = cast(ChecksumAddress, '0x74312363e45DCaBA76c59ec49a7Aa8A65a67EeD3')

with open('utils/x2y2_abi.json', 'r') as f:
    x2y2_abi = json.load(f)

x2y2_contract = w3.eth.contract(address=x2y2_addr, abi=x2y2_abi)

EvProfit_event_sig = w3.keccak(
    text='EvProfit(bytes32,address,address,uint256)'
)  # HexBytes('0xe2c49856b032c255ae7e325d18109bc4e22a2804e2e49a017ec0f59f19cd447b')

EvInventory_event_sig = w3.keccak(
    text=
    'EvInventory(bytes32,address,address,uint256,uint256,uint256,uint256,uint256,address,bytes,(uint256,bytes),(uint8,uint256,uint256,uint256,bytes32,address,bytes,uint256,uint256,uint256,(uint256,address)[]))'
)  # HexBytes('0x3cbb63f144840e5b1b0a38a7c19211d2e89de4d7c5faf8b2d3c1776c302d1d33')

EvCancel_event_sig = w3.keccak(
    text='EvCancel(bytes32)'
)  # HexBytes('0x5b0b06d07e20243724d90e17a20034972f339eb28bd1c9437a71999bd15a1e7a')


class EvProfitDict(TypedDict):
    itemHash: HexBytes
    currency: ChecksumAddress
    to: ChecksumAddress
    amount: int


class EvInventoryDict(TypedDict):
    maker: ChecksumAddress
    taker: ChecksumAddress
    currency: ChecksumAddress
    item: Tuple[int, bytes]
    detail: Tuple[int, int, int, int, bytes, ChecksumAddress, bytes, int, int,
                  int, List[Tuple[int, ChecksumAddress]]]


class Op(IntEnum):
    INVALID = 0,
    COMPLETE_SELL_OFFER = 1,
    COMPLETE_BUY_OFFER = 2,
    CANCEL_OFFER = 3,
    BID = 4,
    COMPLETE_AUCTION = 5,
    REFUND_AUCTION = 6,
    REFUND_AUCTION_STUCK_ITEM = 7


class Fee(TypedDict):
    percentage: float
    to: ChecksumAddress


class SettleDetail(TypedDict):
    op: Op
    orderIdx: int
    itemIdx: int
    price: float
    itemHash: HexBytes
    executionDelegate: ChecksumAddress
    dataReplacement: bytes
    bidIncentivePct: int
    aucMinIncrementPct: int
    aucIncDurationSecs: int
    fee: List[Fee]


class EvInventoryEvent():
    detail: SettleDetail

    def __init__(self, ev_inventory_dict: EvInventoryDict):
        self.maker = ev_inventory_dict['maker']
        self.taker = ev_inventory_dict['taker']
        self.currency = ev_inventory_dict['currency']

        data = ev_inventory_dict['item'][1].hex()
        self.item = {
            'price': ev_inventory_dict['item'][0] / 10**18,
            'data': {
                'token': cast(HexAddress, '0x' + data[64 * 2 + 24:64 * 3]),
                'identifier': int(data[64 * 3:64 * 4], 16)
            }
        }

        detail = ev_inventory_dict['detail']
        self.detail = {
            'op':
            cast(Op, detail[0]),
            'orderIdx':
            detail[1],
            'itemIdx':
            detail[2],
            'price':
            detail[3] / 10**18,
            'itemHash':
            HexBytes(detail[4]),
            'executionDelegate':
            detail[5],
            'dataReplacement':
            detail[6],
            'bidIncentivePct':
            detail[7],
            'aucMinIncrementPct':
            detail[8],
            'aucIncDurationSecs':
            detail[9],
            'fee': [{
                'percentage': fee[0] / 10000,
                'to': fee[1]
            } for fee in detail[10]]
        }

    def __repr__(self):
        return str({
            'maker': self.maker,
            'taker': self.taker,
            'currency': self.currency,
            'item': self.item,
            'detail': self.detail
        })


def get_x2y2_tx_balance(ev_inventory: EvInventoryEvent,
                        ev_profit: EvProfitDict,
                        account: HexAddress) -> DealBalance:
    assert ev_inventory.detail['itemHash'] == ev_profit[
        'itemHash'], 'itemHash does not match'

    assert ev_inventory.detail[
        'op'] == Op.COMPLETE_SELL_OFFER, 'not COMPLETE_SELL_OFFER'

    if ev_profit['to'].lower() == account.lower():
        return {
            'eth': ev_profit['amount'] / 10**18,
            'nft_address': ev_inventory.item['data']['token'],
            'nft_amount': 1
        }
    else:
        return {
            'eth': -ev_inventory.item['price'],
            'nft_address': ev_inventory.item['data']['token'],
            'nft_amount': 1
        }
