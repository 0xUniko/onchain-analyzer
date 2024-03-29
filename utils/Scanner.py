from typing import Tuple
import httpx, datetime, time
from dotenv import dotenv_values
from web3 import Web3, HTTPProvider
from web3.middleware.geth_poa import geth_poa_middleware
from tenacity import retry
from tenacity.wait import wait_random
from tenacity.stop import stop_after_attempt

api_key = dotenv_values()["API_KEY"]
if api_key is None:
    raise ValueError("API_KEY is required")
# api = "https://api.etherscan.io/api"
# api = 'https://api.bscscan.com/api'
# api = 'https://api-test.bscscan.com/api'
# endpoint = dotenv_values()['ANKR_BSC_ENDPOINT']
# endpoint = dotenv_values()["ALCHEMY_ETH_API"]
# endpoint = 'https://rpc.ankr.com/eth'
endpoint = dotenv_values()["ENDPOINT"]
assert endpoint is not None, "endpoint not config"
api = endpoint + "api"
rpc = dotenv_values()["RPC"]
assert rpc is not None, "rpc not set"
proxy = "http://127.0.0.1:10809"

w3 = Web3(HTTPProvider(rpc))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


class Scanner:
    def __init__(self, api=api, key=api_key, proxies=proxy):
        self.api = api
        self.key = key
        self.proxies = proxies

    @retry(stop=stop_after_attempt(10), wait=wait_random(min=1, max=1.5), reraise=True)
    @staticmethod
    def get_start_end_block_of_date(
        date: datetime.date, proxies=None
    ) -> Tuple[int, int]:
        """
        The block starts after the date starts
        """

        start_timestamp_of_date = int(time.mktime(time.strptime(str(date), "%Y-%m-%d")))
        end_timestamp_of_date = (
            int(
                time.mktime(
                    time.strptime(str(date + datetime.timedelta(days=1)), "%Y-%m-%d")
                )
            )
            - 1
        )

        with Scanner(proxies=proxy) as scanner:
            start_block_no = int(
                scanner.scan(
                    "block",
                    "getblocknobytime",
                    timestamp=start_timestamp_of_date,
                    closest="after",
                )
            )
            end_block_no = (
                int(
                    scanner.scan(
                        "block",
                        "getblocknobytime",
                        timestamp=end_timestamp_of_date,
                        closest="before",
                    )
                )
                if end_timestamp_of_date < time.time()
                else w3.eth.block_number
            )

        return start_block_no, end_block_no

    @retry(stop=stop_after_attempt(1), wait=wait_random(min=1, max=1.5), reraise=True)
    def scan(self, module: str, action: str, **kwargs):
        params = {"module": module, "action": action, "apiKey": self.key, **kwargs}

        return self.client.get(url=self.api, params=params).json()["result"]

    @retry(stop=stop_after_attempt(1), wait=wait_random(min=1, max=1.5), reraise=True)
    async def scan_async(self, module: str, action: str, **kwargs):
        params = {"module": module, "action": action, "apiKey": self.key, **kwargs}

        res = await self.async_client.get(url=self.api, params=params)

        return res.json()["result"]

    def __enter__(self):
        self.client = httpx.Client(proxies=self.proxies, timeout=None)
        return self

    async def __aenter__(self):
        self.async_client = httpx.AsyncClient(proxies=self.proxies, timeout=None)
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.client.close()
        return False

    async def __aexit__(self, exc_type, exc_value, trace):
        await self.async_client.aclose()
        return False
