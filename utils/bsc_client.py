import httpx
from dotenv import dotenv_values
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from tenacity import retry, wait_random, stop_after_attempt

api_key = dotenv_values()['BSCSCAN_API_KEY']
api = 'https://api.bscscan.com/api'
# api = 'https://api-test.bscscan.com/api'
endpoint = dotenv_values()['ANKR_BSC_ENDPOINT']

w3 = Web3(HTTPProvider(endpoint))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


class Scanner():
    def __init__(self, api=api, key=api_key):
        self.api = api
        self.key = key

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
        self.client = httpx.Client(proxies='http://127.0.0.1:10809')
        return self

    async def __aenter__(self):
        self.client = httpx.AsyncClient(proxies='http://127.0.0.1:10809')
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.client.close()
        return False

    async def __aexit__(self, exc_type, exc_value, trace):
        await self.client.aclose()
        return False