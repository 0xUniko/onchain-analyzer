from typing import Tuple
import httpx, datetime, time, os, json
from dotenv import dotenv_values
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from tenacity import retry, wait_random, stop_after_attempt
import pandas as pd

api_key = dotenv_values()['BSCSCAN_API_KEY']
api = 'https://api.bscscan.com/api'
# api = 'https://api-test.bscscan.com/api'
endpoint = dotenv_values()['ANKR_BSC_ENDPOINT']

w3 = Web3(HTTPProvider(endpoint))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


class Scanner():
    def __init__(self, api=api, key=api_key, proxies=None):
        self.api = api
        self.key = key
        self.proxies = proxies

    @retry(stop=stop_after_attempt(10),
           wait=wait_random(min=1, max=1.5),
           reraise=True)
    def get_start_end_block_of_date(date: datetime.date) -> Tuple[int, int]:
        '''
        The block starts after the date starts
        '''

        start_timestamp_of_date = int(
            time.mktime(time.strptime(str(date), '%Y-%m-%d')))
        end_timestamp_of_date = int(
            time.mktime(
                time.strptime(str(date + datetime.timedelta(days=1)),
                              '%Y-%m-%d'))) - 1

        with Scanner() as scanner:
            start_block_no = int(
                scanner.scan('block',
                             'getblocknobytime',
                             timestamp=start_timestamp_of_date,
                             closest='after'))
            end_block_no = int(
                scanner.scan('block',
                             'getblocknobytime',
                             timestamp=end_timestamp_of_date,
                             closest='before')
            ) if end_timestamp_of_date < time.time() else w3.eth.block_number

        return start_block_no, end_block_no

    @retry(stop=stop_after_attempt(1),
           wait=wait_random(min=1, max=1.5),
           reraise=True)
    def scan(self, module: str, action: str, **kwargs):
        params = {
            'module': module,
            'action': action,
            'apiKey': self.key,
            **kwargs
        }

        return self.client.get(url=self.api, params=params).json()['result']

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
            new_txs = self.scan('account',
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

        startblock, endblock = Scanner.get_start_end_block_of_date(date)

        if os.path.exists(cache_txs):
            txs = pd.read_feather(cache_txs)

            last_tx = sorted([
                f for f in os.listdir(dirname)
                if len(f) == 14 and f[-3:] == 'csv'
            ])[-1][:10]

            if str(date) == last_tx:
                if not txs.empty:
                    startblock = txs.iloc[-1]['blockNumber']
            else:
                txs.set_index('hash', inplace=True)
                return txs
        else:
            txs = None

        endblock += 1
        print('startblock:', startblock, 'endblock:', endblock)

        listdir = os.listdir(os.path.join(dirname, 'tmp'))
        new_txs_collector = []
        flag = True

        while flag:
            print('startblock:', startblock)

            tmp = str(startblock) + '.json'
            if tmp in listdir:
                with open(f'utils/storage/{name}/tmp/{tmp}', 'r') as f:
                    new_txs = json.load(f)
            else:
                new_txs = self.scan('account',
                                    'txlist',
                                    address=address,
                                    startblock=startblock,
                                    endblock=endblock)

                with open(f'utils/storage/{name}/tmp/{tmp}', 'w') as f:
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

        txs = pd.concat([txs, pd.DataFrame(new_txs_collector)
                         ]) if txs else pd.DataFrame(new_txs_collector)
        if new_txs_collector:
            txs.to_feather(cache_txs)

        txs.set_index('hash', inplace=True)
        return txs

    @retry(stop=stop_after_attempt(1),
           wait=wait_random(min=1, max=1.5),
           reraise=True)
    async def scan_async(self, module: str, action: str, **kwargs):
        params = {
            'module': module,
            'action': action,
            'apiKey': self.key,
            **kwargs
        }

        res = await self.client.get(url=self.api, params=params)

        return res.json()['result']

    def __enter__(self):
        self.client = httpx.Client(proxies=self.proxies, timeout=None)
        return self

    async def __aenter__(self):
        self.client = httpx.AsyncClient(proxies=self.proxies, timeout=None)
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.client.close()
        return False

    async def __aexit__(self, exc_type, exc_value, trace):
        await self.client.aclose()
        return False