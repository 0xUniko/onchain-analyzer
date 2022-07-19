from utils.Scanner import w3
from utils.SimpleTxsGetter import SimpleTxsGetter
from utils.LogsGetter import LogsGetter
from eth_typing.evm import ChecksumAddress
from eth_typing.encoding import HexStr
from web3.types import TxData
from hexbytes import HexBytes
import pandas as pd
from tqdm import tqdm
import json
from typing import Sequence, cast

seaport_addr = cast(ChecksumAddress,
                    '0x00000000006c3852cbEf3e08E8dF289169EdE581')

OrderFulfilled_event_sig = w3.keccak(
    text=
    'OrderFulfilled(bytes32,address,address,address,(uint8,address,uint256,uint256)[],(uint8,address,uint256,uint256,address)[])'
)  #HexBytes(0x9d9af8e38d66c62e2c12f0225249fd9d721c54b83f48d9352c97c6cacdcb6f31)

with open('utils/seaport_abi.json', 'r') as f:
    seaport_abi = json.load(f)

seaport_contract = w3.eth.contract(address=seaport_addr, abi=seaport_abi)


class SpentItem():

    def __init__(self, data: str):
        self.itemType = int(data[:64], 16)
        self.token = '0x' + data[88:64 * 2]
        self.identifier = int(data[64 * 2:64 * 3], 16)
        self.amount = int(data[64 * 3:64 * 4], 16)


class ReceivedItem():

    def __init__(self, data: str):
        self.itemType = int(data[:64], 16)
        self.token = '0x' + data[88:64 * 2]
        self.identifier = int(data[64 * 2:64 * 3], 16)
        self.amount = int(data[64 * 3:64 * 4], 16)
        self.recipient = '0x' + data[64 * 4:64 * 5]


class OrderFulfilledEvent():

    def __init__(self, topics: Sequence[HexBytes], data: HexStr):
        self.offerer = topics[1]
        self.zone = topics[2]
        data_hex = data[2:]
        self.orderHash = '0x' + data_hex[:64]
        self.recipient = '0x' + data_hex[89:128]

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


def get_deal_price_from_seaport_tx(seaport_tx: TxData) -> float:
    if 'hash' in seaport_tx:
        logs = pd.DataFrame(
            w3.eth.get_transaction_receipt(seaport_tx['hash'])['logs'])

        for _, log in logs.iterrows():
            if log['topics'][0].hex() == OrderFulfilled_event_sig:
                order_fulfilled_event = OrderFulfilledEvent(
                    topics=log['topics'], data=log['data'])

                return max([
                    consi.amount / 10**18
                    for consi in order_fulfilled_event.consideration
                ])

        raise Exception("This transaction does not have OrderFulfilled event")

    raise Exception("This transaction does not have hash")


def get_nft_ath(nft_addr: ChecksumAddress) -> float:
    with SimpleTxsGetter() as txs_getter:
        txs = txs_getter.all_txs(address=nft_addr)

    with LogsGetter() as logs_getter:
        logs = logs_getter.get_token_logs(nft_addr)

    exterier_logs = logs.loc[~logs['transactionHash'].isin(txs['hash'])]

    nft_txs = []
    for hash in tqdm(exterier_logs['transactionHash']):
        tx = w3.eth.get_transaction(hash)
        nft_txs.append(tx)
    # nft_txs = pd.DataFrame(nft_txs)
    # seaport_txs = nft_txs.loc[nft_txs['to'] == seaport_addr]

    # return seaport_txs
    return 1