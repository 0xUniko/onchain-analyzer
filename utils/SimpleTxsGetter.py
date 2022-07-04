import warnings
import pandas as pd
from utils.Scanner import Scanner
from eth_typing.evm import HexAddress


class SimpleTxsGetter():

    def __init__(self, proxies='http://127.0.0.1:10809'):
        self.proxies = proxies
        self.scanner = Scanner(proxies=proxies).__enter__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.scanner.__exit__(exc_type, exc_value, trace)
        return False

    def all_txs(self, address: HexAddress):
        new_txs_collector = []
        startblock = 1

        while True:
            print('startblock:', startblock)

            new_txs = self.scanner.scan('account',
                                        'txlist',
                                        address=address,
                                        startblock=startblock)
            if not new_txs:
                warnings.warn(f'startblock {startblock} is empty!')

            new_txs_collector = [
                tx for tx in new_txs_collector
                if tx['blockNumber'] != startblock
            ]

            if new_txs:
                new_txs_collector.extend(
                    [tx for tx in new_txs if tx['isError'] != '1'])

            if new_txs == None or len(new_txs) != 10000:
                break
            else:
                startblock = new_txs[-1]['blockNumber']

        return pd.DataFrame(new_txs_collector)