#%%
from typing import TypedDict
from utils.Scanner import w3, scan
from utils.pancake_utils import pancake_factory_address, pairCreated_topic, wbnb_topic, pancake_router_contract, wbnb_addr
from utils.get_pairCreated_logs import get_pairCreated_logs
import pandas as pd
import datetime, time, json

with open('utils/pancake_lp_abi.json', 'r') as f:
    pancake_lp_abi = json.load(f)

# %%
# logs = get_pairCreated_logs(datetime.date(2021, 12, 26))
logs = get_pairCreated_logs(datetime.date(2021, 12, 31))
# logs = get_pairCreated_logs(datetime.date.today() - datetime.timedelta(days=1))
# %%
len(logs)
# %%
logs.iloc[34]['topics']

# %%
no = 258
lp_addr = '0x' + logs.iloc[no]['data'][26:66]
topics = logs.iloc[no]['topics'][2:-2].split("', '")
token = ('0x' +
         topics[1][26:66]) if topics[1] != wbnb_topic else ('0x' +
                                                            topics[2][26:66])
print(token)
# %%
token
# %%
token_tx_list = scan('account',
                     'tokentx',
                     contractaddress=token,
                     address=lp_addr)
bnb_tx_list = scan('account',
                   'tokentx',
                   contractaddress=wbnb_addr,
                   address=lp_addr)
# %%
print(len(token_tx_list), len(bnb_tx_list))
# %%
for index, event in logs.iterrows():
    try:
        lp_addr = '0x' + event['data'][26:66]
        token = '0x' + event['topics'][1][26:66] if event['topics'][
            0] != wbnb_topic else '0x' + event['topic'][2][26:66]

        token_tx_list = scan('account',
                             'tokentx',
                             contractaddress=token,
                             address=lp_addr)
        bnb_tx_list = scan('account',
                           'tokentx',
                           contractaddress=wbnb_addr,
                           address=lp_addr)

        if len(token_tx_list) >= 700 or len(bnb_tx_list) >= 700:
            print(index)

    except Exception as e:
        print(index, '      ', e)
    finally:
        time.sleep(0.21)

# %%
lp_contract = w3.eth.contract(address=w3.toChecksumAddress(lp_addr),
                              abi=pancake_lp_abi)
# %%
lp_contract.functions.getReserves().call()


# %%
class Stat(dict):
    init_liquidity: int
    liquidity: int
    buy_cnt: int
    sell_cnt: int
    owner_total_buy: int
    owner_total_sell: int
    total_buy_except_owner: int
    total_sell_except_owner: int


# %%
def filter_add_liquidity(tx, token: str) -> bool:
    try:
        input = pancake_router_contract.decode_function_input(tx['input'])

        return input[0].abi['name'] == 'addLiquidityETH' and input[1][
            'token'].lower() == token.lower()
    except:
        return False


# %%
def new_token_stat(pair_created_event) -> Stat:
    lp_addr = '0x' + pair_created_event['data'][26:66]
    token = pair_created_event['topics'][2] if pair_created_event['topic'][
        1] == wbnb_topic else pair_created_event['topics'][1]
    create_pair_tx = w3.eth.get_transaction(
        pair_created_event['transactionHash'])
    owner = create_pair_tx['from']

    owner_tx = scan('account',
                    'txlist',
                    address=owner,
                    startbock=create_pair_tx['blockNumber'])

    add_liquidity_bnb = int(
        list(filter(lambda x: filter_add_liquidity(x, token),
                    owner_tx))[0]['value'])


# %%
logs.iloc[0]
# %%
# 创建池子时添加的流动性
# 之后的交易记录（看看卖出记录，注意卖出是不在代币合约里记录里的，有approve但是没有卖出就大概率貔貅）
# 怎么防燃烧池？
# 所以说关键就是买卖记录了（？），找法：博饼的交易记录里筛选（这个可以排除了吧），代币的内部转账，lptoken的bep20转账
# 初始池子bnb，现在池子bnb，买入次数，卖出次数，创建人买入总量，创建人卖出总量，创建人之外买入总量，创建人之外卖出总量
# 在开始的时候几分钟十几分钟之内冲进去赚一点收益就跑的策略，要判断什么条件进什么时候跑，怎么判断貔貅，