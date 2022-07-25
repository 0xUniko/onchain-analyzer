from utils.Scanner import w3
from utils.addr_trac_padding import addr_trac
from eth_typing.evm import ChecksumAddress, HexAddress
from eth_typing.encoding import HexStr
from web3.types import TxData
from hexbytes import HexBytes
import pandas as pd
from tqdm import tqdm
import json
from enum import IntEnum
from typing import Sequence, cast, TypedDict

seaport_addr = cast(ChecksumAddress,
                    '0x00000000006c3852cbEf3e08E8dF289169EdE581')

# weth = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'

OrderFulfilled_event_sig = w3.keccak(
    text=
    'OrderFulfilled(bytes32,address,address,address,(uint8,address,uint256,uint256)[],(uint8,address,uint256,uint256,address)[])'
)  #HexBytes(0x9d9af8e38d66c62e2c12f0225249fd9d721c54b83f48d9352c97c6cacdcb6f31)

with open('utils/seaport_abi.json', 'r') as f:
    seaport_abi = json.load(f)

seaport_contract = w3.eth.contract(address=seaport_addr, abi=seaport_abi)


class ItemType(IntEnum):
    NATIVE = 0,
    ERC20 = 1,
    ERC721 = 2,
    ERC1155 = 3,
    ERC721_WITH_CRITERIA = 4,
    ERC1155_WITH_CRITERIA = 5


class SpentItem():
    itemType: ItemType
    token: HexAddress
    identifier: int
    amount: int

    def __init__(self, data: str):
        self.itemType = cast(ItemType, int(data[:64], 16))
        self.token = cast(HexAddress, '0x' + data[88:64 * 2])
        self.identifier = int(data[64 * 2:64 * 3], 16)
        self.amount = int(data[64 * 3:64 * 4], 16)

    def __repr__(self):
        return str({
            'itemType': self.itemType,
            'token': self.token,
            'identifier': self.identifier,
            'amount': self.amount
        })


class ReceivedItem():
    itemType: ItemType
    token: HexAddress
    identifier: int
    amount: int
    recipient: HexAddress

    def __init__(self, data: str):
        self.itemType = cast(ItemType, int(data[:64], 16))
        self.token = cast(HexAddress, '0x' + data[88:64 * 2])
        self.identifier = int(data[64 * 2:64 * 3], 16)
        self.amount = int(data[64 * 3:64 * 4], 16)
        self.recipient = cast(HexAddress, '0x' + data[64 * 4 + 24:64 * 5])

    def __repr__(self):
        return str({
            'itemType': self.itemType,
            'token': self.token,
            'amount': self.amount,
            'recipient': self.recipient
        })


class DealBalance(TypedDict):
    eth: float
    nft_amount: int
    nft_address: HexAddress


class OrderFulfilledEvent():

    def __init__(self, topics: Sequence[HexBytes], data: HexStr):
        self.offerer = addr_trac(topics[1])
        self.zone = topics[2]
        data_hex = data[2:]
        self.orderHash = '0x' + data_hex[:64]
        self.recipient = cast(HexAddress, '0x' + data_hex[88:128])

        self.offer_length = int(data_hex[64 * 4:64 * 5], 16)
        self.offer = [
            SpentItem(data_hex[64 * (5 + 4 * i):64 * (5 + 4 * (i + 1))])
            for i in range(self.offer_length)
        ]

        self.consideration_length = int(
            data_hex[64 * (5 + 4 * self.offer_length):64 *
                     (6 + 4 * self.offer_length)], 16)

        self.consideration = [
            ReceivedItem(data_hex[64 * (6 + 4 * self.offer_length + 5 * i):64 *
                                  (6 + 4 * self.offer_length + 5 * (i + 1))])
            for i in range(self.consideration_length)
        ]

    def get_deal_price(self):
        return max([consi.amount / 10**18 for consi in self.consideration])

    # def get_deal_balance(self, account: HexAddress) -> DealBalance:
    #     assert self.offer_length == 1, 'multiple offers should use this function'

    #     if self.offerer == account:
    #         match self.offer[0].itemType:
    #             case ItemType.NATIVE:
    #                 pass
    #             case ItemType.
    #         if self.offer[0].token == weth:
    #             eth = -self.offer[0].amount / 10**18

    #         return {
    #             'eth':
    #             -sum([
    #                 offer.amount / 10**18
    #                 for offer in self.offer if offer.token == weth
    #             ]),
    #             'nft_amount':
    #             sum([
    #                 consi.amount for consi in self.consideration
    #                 if consi.recipient == account
    #             ])
    #         }
    #     elif self.recipient == account:
    #         coeff = 1
    #     else:
    #         raise ValueError(
    #             "the input account does not match either offerer or recipient")

    #     return coeff * self.get_deal_price()

    def __repr__(self):
        return str({
            'offerer': self.offerer,
            'zone': self.zone,
            'orderHash': self.orderHash,
            'recipient': self.recipient,
            'offer': self.offer,
            'consideration': self.consideration
        })


def get_deal_price_from_seaport_tx(seaport_tx: TxData) -> float:
    if 'hash' in seaport_tx:
        logs = pd.DataFrame(
            w3.eth.get_transaction_receipt(seaport_tx['hash'])['logs'])

        for _, log in logs.iterrows():
            if log['topics'][0].hex() == OrderFulfilled_event_sig:
                return OrderFulfilledEvent(topics=log['topics'],
                                           data=log['data']).get_deal_price()

        raise Exception("This transaction does not have OrderFulfilled event")

    raise Exception("This transaction does not have hash")


# def get_nft_ath(nft_addr: ChecksumAddress) -> float:
#     with CompleteGetter() as txs_getter:
#         txs = txs_getter.get_all(address=nft_addr)

#     with LogsGetter() as logs_getter:
#         logs = logs_getter.get_token_logs(nft_addr)

#     exterier_logs = logs.loc[~logs['transactionHash'].isin(txs['hash'])]

#     nft_txs = []
#     for hash in tqdm(exterier_logs['transactionHash']):
#         tx = w3.eth.get_transaction(hash)
#         nft_txs.append(tx)
#     # nft_txs = pd.DataFrame(nft_txs)
#     # seaport_txs = nft_txs.loc[nft_txs['to'] == seaport_addr]

#     # return seaport_txs
#     return 1