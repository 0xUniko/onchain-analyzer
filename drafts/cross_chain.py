#%%
import httpx
from dotenv import dotenv_values
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

#%%
api_key = dotenv_values()['BSCSCAN_API_KEY']
endpoint = dotenv_values()['ANKR_BSC_ENDPOINT']
url = 'https://api.bscscan.com/api'

w3 = Web3(HTTPProvider(endpoint))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# POLYGON
# %%
api_key = dotenv_values()['POLYGONSCAN_API_KEY']
endpoint = dotenv_values()['ANKR_POLYGON_ENDPOINT']
url = 'https://api.polygonscan.com/api'

w3 = Web3(HTTPProvider(endpoint))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
# The account who signed the transaction
#%%
account = '0x25eacdd7b45639142110874150ada35908046325'
# %%
params = {
    'module': 'account',
    'action': 'txlist',
    'address': account,
    'apiKey': api_key,
    'startblock': 0,
    'endblock': 'latest'
}

tx_list = httpx.get(url=url, params=params).json()['result']
# %%
len(tx_list)
# %%
in_list = list(filter(lambda x: x['to'] == account, tx_list))
# %%
list(
    map(
        lambda x: {
            'form': x['from'],
            'value': w3.fromWei(int(x['value']), 'ether'),
            'block_number': x['blockNumber']
        }, in_list))

# the XSwap contract
# %%
contract_addr = '0x50a64d05bB8618D8d96A83CbBb12b3044ec3489A'
w3.keccak(text='batchClaim(uint256[],address,bytes[])')
# %%
params = {
    'module': 'account',
    'action': 'txlist',
    'address': contract_addr,
    'apiKey': api_key,
    'startblock': 0,
    'endblock': 'latest'
}

tx_list = httpx.get(url=url, params=params).json()['result']
# %%
import json
with open('utils/xswap_abi.json') as f:
    abi = json.load(f)

xswap_contract = w3.eth.contract(address=contract_addr, abi=abi)
# %%
import pandas as pd

calls = pd.DataFrame(
    list(
        map(
            lambda x:
            (x['from'], xswap_contract.decode_function_input(x['input'])[0].
             abi['name']), tx_list[1:])))

calls.columns = ['caller', 'function']

# %%
top_caller = calls['caller'].value_counts().index[0]
# %%
calls.loc[calls['caller'] == top_caller, 'function'].value_counts()

# %%
calls['function'].value_counts()
# %%
c_and_f = list(
    map(
        lambda x:
        (x['from'], xswap_contract.decode_function_input(x['input'])),
        tx_list[1:]))

# %%
my_calls = list(
    filter(lambda x: x[0] == '0x7291c802d5eabf172c81b5eff0e925e8eccf3d2b',
           c_and_f))

# %%
w3.keccak(text='swap(tuple,bytes,tuple)')

# %%
calls.loc[calls['caller'] == '0x7291c802d5eabf172c81b5eff0e925e8eccf3d2b',
          'function']

# FIND THE AGGREGATOR
# %%
params = {
    'module': 'logs',
    'action': 'getLogs',
    'address': contract_addr,
    'topic0': w3.keccak(text='AggregatorSet(address)').hex()
}

httpx.get(url=url, params=params).json()['result']
# %%
print(w3)