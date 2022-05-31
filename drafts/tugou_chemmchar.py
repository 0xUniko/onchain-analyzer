#%%
from utils.Scanner import w3, scan
from utils.pancake_utils import pancake_router_contract, wbnb_addr, pancake_router_topic

cheemchar = '0x826fab68b79af8a31be6dda766437ddddc540dfd'
abi = scan('contract', 'getabi', address=cheemchar)
contract = w3.eth.contract(address=w3.toChecksumAddress(cheemchar), abi=abi)

lp_addr = '0x77860880ac11afa8f715a5a373de277eab22c104'
lp_abi = scan('contract', 'getabi', address=lp_addr)
lp_contract = w3.eth.contract(address=w3.toChecksumAddress(lp_addr),
                              abi=lp_abi)

owner = '0x702Bb112D78b454cCEa36cD8E26c0CDfAc8C469D'
# %%
owner_tx = scan('account', 'txlist', address=owner, startbock=13787501)

# %%
token_tx_list = scan('account',
                     'tokentx',
                     contractaddress=cheemchar,
                     address=lp_addr)
bnb_tx_list = scan('account',
                   'tokentx',
                   contractaddress=wbnb_addr,
                   address=lp_addr)

# %%
lp_logs = scan('logs', 'getLogs', address=lp_addr)
# %%
len(lp_logs)
# %%
tx = w3.eth.get_transaction(token_tx_list[-5]['hash'])
pancake_router_contract.decode_function_input(tx['input'])[0].abi['name']

# %%
tx = w3.eth.get_transaction(lp_logs[-5]['transactionHash'])
pancake_router_contract.decode_function_input(tx['input'])
# %%
list(
    filter(lambda x: x['hash'] == lp_logs[-5]['transactionHash'],
           token_tx_list))

# %%
len(bnb_tx_list)
# %%
list(filter(lambda x: x['hash'] == lp_logs[-5]['transactionHash'],
            bnb_tx_list))


# %%
def decode_pair_event(event):
    if event == w3.keccak(text='Mint(address,uint256,uint256)').hex():
        return 'mint'
    if event == w3.keccak(text='Burn(address,uint256,uint256,address)').hex():
        return 'burn'
    if event == w3.keccak(
            text='Swap(address,uint256,uint256,uint256,uint256,address)').hex(
            ):
        return 'swap'
    if event == w3.keccak(text='Sync(uint112,uint112)').hex():
        return 'sync'
    return None


# %%
list(map(lambda x: decode_pair_event(x['topics'][0]), lp_logs))

# %%
len(
    list(filter(lambda x: decode_pair_event(x['topics'][0]) == 'swap',
                lp_logs)))
# %%
next(filter(lambda x: decode_pair_event(x['topics'][0]) == 'swap', lp_logs))

# %%
lp_logs[-5]
# %%
buy_cnt = 0
sell_cnt = 0
owner_total_buy = 0
owner_total_sell = 0
total_buy_except_owner = 0
total_sell_except_owner = 0

token_tx_list = scan('account',
                     'tokentx',
                     contractaddress=cheemchar,
                     address=lp_addr)
bnb_tx_list = scan('account',
                   'tokentx',
                   contractaddress=wbnb_addr,
                   address=lp_addr)

swap_logs = scan(
    'logs',
    'getLogs',
    address=lp_addr,
    topic0=w3.keccak(
        text='Swap(address,uint256,uint256,uint256,uint256,address)').hex())

for event in swap_logs:
    if pancake_router_topic in event['topics']:
        tx = w3.eth.get_transaction(event['transactionHash'])

# %%
data = '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006a94d74f430000000000000000000000000000000000000000000000000000003294a8d83041e60000000000000000000000000000000000000000000000000000000000000000'
amount0In = data[0:64]
amount1In = data[64:128]
amount0Out = data[128:192]
amount1Out = data[192:]
# %%
int(amount1In, 16)
# %%
print(amount0Out)
int(amount0Out, 16)

# %%
'0x00000000000000000000000010ed43c718714eb63d5aa57b78b54704e256024e' in [
    '0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822',
    '0x00000000000000000000000010ed43c718714eb63d5aa57b78b54704e256024e',
    '0x00000000000000000000000010ed43c718714eb63d5aa57b78b54704e256024e'
]
# %%
# txlist[0]: create contract
# totalSupply: 1000_000_000 * 10 ** 9

# txlist[1]: denounceOwnership

# txlist[2]: burn 500_000_000_000_000_000

# txlist[3]: approve for pancake routerv2
