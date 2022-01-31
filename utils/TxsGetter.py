#%%
from typing import List
from utils.bsc_client import Scanner
import datetime, os, json
import pandas as pd
from tenacity import retry, wait_random, stop_after_attempt


class TxsGetter():
    def __init__(self, proxies=None):
        self.scanner = Scanner(proxies=proxies).__enter__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.scanner.__exit__(exc_type, exc_value, trace)
        return False

    def bep20_txs(self, address=None, contractaddress=None):
        startblock = 0
        txs = []
        flag = True
        rd = 0

        params = {}
        if address != None:
            params['address'] = address
        if contractaddress != None:
            params['contractaddress'] = contractaddress

        while flag:
            print('round:', rd)
            new_txs = self.scanner.scan('account',
                                        'tokentx',
                                        startblock=startblock,
                                        **params)

            txs_hash = [x['hash'] for x in txs]
            txs.extend([tx for tx in new_txs if tx['hash'] not in txs_hash])

            if len(new_txs) != 10000:
                flag = False
            else:
                startblock = new_txs[-1]['blockNumber']
                rd += 1

        return txs

    def all_txs(self,
                date: datetime.date,
                name='pcs_router_txs',
                address='0x10ed43c718714eb63d5aa57b78b54704e256024e'):
        '''
        get all transactions of a date
        '''
        dirname = os.path.join('utils', 'storage', name)

        if not os.path.exists(dirname):
            os.mkdir(dirname)

        cache_txs = os.path.join(dirname, f'{str(date)}.feather')

        if os.path.exists(cache_txs):
            txs: pd.DataFrame = pd.read_feather(cache_txs)

            last_tx = sorted([
                f for f in os.listdir(dirname)
                if len(f) == 18 and f[-7:] == 'feather'
            ])[-1][:10]

            if str(date) == last_tx:
                if not txs.empty:
                    _, endblock = Scanner.get_start_end_block_of_date(date)
                    startblock = txs.iloc[-1]['blockNumber']
            else:
                txs.set_index('hash', inplace=True)
                return txs
        else:
            startblock, endblock = Scanner.get_start_end_block_of_date(date)
            txs = pd.DataFrame()

        print('startblock:', startblock, 'endblock:', endblock)

        listdir = os.listdir(os.path.join(dirname, 'tmp'))
        new_txs_collector = []
        flag = True

        while flag:
            print('startblock:', startblock)

            tmp = str(startblock) + '.json'
            if tmp in listdir:
                with open(os.path.join(dirname, 'tmp', tmp), 'r') as f:
                    new_txs = json.load(f)
            else:
                new_txs = self.scanner.scan('account',
                                            'txlist',
                                            address=address,
                                            startblock=startblock,
                                            endblock=endblock)

                with open(os.path.join(dirname, 'tmp', tmp), 'w') as f:
                    json.dump(new_txs, f)

            new_txs_collector = [
                tx for tx in new_txs_collector
                if tx['blockNumber'] != startblock
            ]

            new_txs_collector.extend(
                [tx for tx in new_txs if tx['isError'] != '1'])

            if len(new_txs) != 10000:
                flag = False
            else:
                startblock = new_txs[-1]['blockNumber']

        txs = pd.concat([txs, pd.DataFrame(new_txs_collector)],
                        ignore_index=True)
        if new_txs_collector:
            txs.to_feather(cache_txs)

        txs.set_index('hash', inplace=True)
        return txs

    def get_txs_by_hashs(self,
                         hashs: List[str],
                         date: datetime.date = datetime.date(2021, 12, 24)):
        today = datetime.date.today()
        txs = []

        while not date > today:
            txs_date = self.all_txs(date=date)

            txs.append(txs_date.loc[[
                hash for hash in hashs if hash in txs_date.index
            ]])

            date += datetime.timedelta(days=1)

        return pd.concat(txs)