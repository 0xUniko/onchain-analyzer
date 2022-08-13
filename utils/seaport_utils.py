from utils.Scanner import w3
from utils.addr_trac_padding import addr_trac
from eth_typing.evm import ChecksumAddress, HexAddress
from eth_typing.encoding import HexStr
from hexbytes import HexBytes
import pandas as pd
import json
from enum import IntEnum
from typing import Sequence, cast, TypedDict

seaport_addr = cast(ChecksumAddress,
                    '0x00000000006c3852cbEf3e08E8dF289169EdE581')

weth = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'

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

    def get_deal_balance(self, account: HexAddress) -> DealBalance:
        '''
        get the account deal balance from a OrderFulfilledEvent
        many limitations exist here and could be removed in future
        '''
        assert self.offerer == account or self.recipient == account, "the input account does not match either offerer or recipient"

        assert pd.Series([o.itemType for o in self.offer
                          ]).nunique() == 1, "multiple itemTypes in offer"

        nft_consi = [
            consi for consi in self.consideration if consi.recipient == account
        ]

        if self.offer[0].itemType == ItemType.NATIVE or self.offer[
                0].itemType == ItemType.ERC20:
            assert self.offer_length == 1, 'the amount of offer in eth is more than one'

            if self.offer[0].itemType == ItemType.ERC20:
                assert self.offer[0].token == weth, 'not pay in eth'

            if self.offerer == account:
                assert all(
                    pd.Series([consi.itemType for consi in nft_consi]) ==
                    ItemType.ERC721), 'not all items are ERC721'

                assert pd.Series([consi.token for consi in nft_consi]).nunique(
                ) == 1, 'more than one collection in the consideration'

                eth = -self.offer[0].amount / 10**18
                nft_amount = sum([consi.amount for consi in nft_consi])
                nft_address = nft_consi[0].token
            else:
                assert len(nft_consi) == 0, 'recipient receives something'
                # maybe could be removed in future
                assert len([
                    consi for consi in self.consideration
                    if consi.itemType == ItemType.NATIVE
                ]) == 0, 'native eth transferred'

                eth = (self.offer[0].amount - sum([
                    consi.amount for consi in self.consideration
                    if consi.itemType == ItemType.ERC20 and consi.token == weth
                ])) / 10**18

                nft_offer_consi = [
                    consi for consi in self.consideration
                    if consi.recipient == self.offerer
                ]
                # maybe could be removed in future
                assert len(
                    nft_offer_consi
                ) == 1, 'recipient gives nothing or more than one thing'

                nft_amount = nft_offer_consi[0].amount
                nft_address = nft_offer_consi[0].token

        elif self.offer[0].itemType == ItemType.ERC721:
            assert pd.Series([
                o.token for o in self.offer
            ]).nunique() == 1, 'more than one collection are traded'
            nft_address = self.offer[0].token

            nft_amount = sum([o.amount for o in self.offer])

            if self.offerer == account:
                # maybe could be removed in future
                assert len(
                    nft_consi
                ) == 1, 'recipient receives nothing or more than one thing'

                eth = nft_consi[0].amount / 10**18
            else:
                # maybe could be removed in future
                assert len(
                    nft_consi
                ) == 0, 'recipient should receive nothing when gives eth'

                eth = -sum([consi.amount
                            for consi in self.consideration]) / 10**18

        else:
            raise ValueError(f'the itemType is f{self.offer[0].itemType}')

        return {
            'eth': eth,
            'nft_amount': nft_amount,
            'nft_address': nft_address
        }

    def __repr__(self):
        return str({
            'offerer': self.offerer,
            'zone': self.zone,
            'orderHash': self.orderHash,
            'recipient': self.recipient,
            'offer': self.offer,
            'consideration': self.consideration
        })
