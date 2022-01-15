import httpx
from dotenv import dotenv_values
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from tenacity import retry, wait_random, stop_after_attempt

api_key = dotenv_values()['BSCSCAN_API_KEY']
url = 'https://api.bscscan.com/api'
endpoint = dotenv_values()['ANKR_BSC_ENDPOINT']

w3 = Web3(HTTPProvider(endpoint))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


class Scanner():
    def __init__(self):
        self.client = httpx.Client()

    @retry(stop=stop_after_attempt(1),
           wait=wait_random(min=1, max=1.5),
           reraise=True)
    def scan(self, module: str, action: str, **kwargs):
        params = {
            'module': module,
            'action': action,
            'apiKey': api_key,
            **kwargs
        }

        return self.client.get(url=url, params=params).json()['result']

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.client.close()
        return False
