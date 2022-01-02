import httpx, pandas
from dotenv import dotenv_values
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

api_key = dotenv_values()['POLYGONSCAN_API_KEY']
endpoint = dotenv_values()['ANKR_POLYGON_ENDPOINT']
url = 'https://api.polygonscan.com/api'

w3 = Web3(HTTPProvider(endpoint))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)