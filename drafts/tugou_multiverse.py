# %%
import datetime, time
import pandas as pd

from utils.Scanner import Scanner, w3
from utils.TxsGetter import TxsGetter
from utils.pancake_utils import pancake_router_contract, wbnb_addr, busd_addr, bsc_usd_addr, dai_addr, doge_addr, pancake_router_topic, pancake_router_address, router_abi, router_input_decoder
from utils.LogsGetter import LogsGetter
from utils.pancake_utils import mint_topic, burn_topic, swap_topic, sync_topic, approval_topic, transfer_topic, hex_to_topic_name, decode_balance

mvs = '0x98Afac3b663113D29dc2Cd8C2d1d14793692F110'
mvs_topic = '0x000000000000000000000000' + mvs[2:].lower()
pair_addr = '0x4ff4714572dc36392f86bb1d62af79a081e463f8'
pair_addrs = [
    # mvs-busd
    '0x0dfa50c4b16d047f87a27a60247c9958c7b8547e',
    # bsc-usd-mvs
    '0x013f9002e5029b1d44dbcd90769e28b1166d57ac',
    # mvs-doge
    '0xa56c3ccaddad61c2e4cb9fd6d10ef60595adf9e2',
    # mvs-wbnb
    '0x4ff4714572dc36392f86bb1d62af79a081e463f8'
]
mvs_start_date = datetime.date(2021, 12, 24)
# %%
pairCreated_logs = get_pairCreated_logs()
create_mvs_events = [
    log for _, log in pairCreated_logs.iterrows()
    if log['topic1'] == mvs_topic or log['topic2'] == mvs_topic
]
pair_addrs = ['0x' + x['data'][26:66] for x in create_mvs_events]


# %%
def is_add_liquidity(input):
    method_name = pancake_router_contract.decode_function_input(
        input)[0].abi['name']
    return method_name == 'addLiquidity' or method_name == 'addLiquidityETH'


# %%
def token_tx_filter(tx, token=mvs):
    func, data = decode_function_input(router_abi, tx['input'])

    if func == 'swapExactTokensForTokens':
        pass

    if func == 'addLiquidity':
        return data['tokenA'] == mvs or data['tokenB'] == mvs

    if func == 'addLiquidityETH':
        return data['token'] == mvs

    # if func.abi['name']==''


# %%
# calculate the daily statistics
date = datetime.date(2021, 12, 24)
today = datetime.date.today()

swap_cnt = pd.Series([], dtype=int)
logs_cnt = pd.Series([], dtype=int)

while not date > today:
    start_timestamp_of_date = int(
        time.mktime(time.strptime(str(date), '%Y-%m-%d')))

    end_timestamp_of_date = int(
        time.mktime(
            time.strptime(str(date + datetime.timedelta(days=1)),
                          '%Y-%m-%d'))) - 1

    swap_cnt[str(date)] = len(mvs_transfer_logs[
        mvs_transfer_logs['timeStamp'].map(lambda x: start_timestamp_of_date <=
                                           int(x) <= end_timestamp_of_date)])

    logs_cnt[str(date)] = len(mvs_logs[mvs_logs['timeStamp'].map(
        lambda x: start_timestamp_of_date <= int(x) <= end_timestamp_of_date)])

    date += datetime.timedelta(days=1)

# %%
logs_cnt.hist()
# %%
swap_cnt.hist()
# %%
# verify that my filter function (filter by transaction input) match the pairs logs
hashs = []
hashs.extend(mvs_logs.loc[mvs_logs['timeStamp'].map(lambda x: str(
    datetime.date.fromtimestamp(x)) == '2021-12-30'), 'transactionHash'])
for log in pair_logs:
    hashs.extend(log.loc[log['timeStamp'].map(lambda x: str(
        datetime.date.fromtimestamp(x)) == '2021-12-30'), 'transactionHash'])
hashs = set(hashs)
print(len(hashs))
# %%
with TxsGetter() as txs_getter:
    txs = txs_getter.get_router_swap_txs_by_token(mvs,
                                                  datetime.date(2021, 12, 30),
                                                  datetime.date(2021, 12, 30))
# %%
set(txs.index).issubset(hashs)
# %%

# %%
# 创建合约之后转账给了0x502fbF208e37A5EE869D925384f8109422823bD0
# 0x502fbf208e37a5ee869d925384f8109422823bd0 approve for router

# swapExactTokensForTokens                                     19204
# swapExactETHForTokens                                        18995
# swapExactTokensForETHSupportingFeeOnTransferTokens           12045
# swapExactTokensForTokensSupportingFeeOnTransferTokens        11960
# swapETHForExactTokens                                        11830
# swapExactTokensForETH                                        10053
# swapExactETHForTokensSupportingFeeOnTransferTokens            6837
# swapTokensForExactTokens                                      6175
# swapTokensForExactETH                                         1039
# addLiquidityETH                                                709
# addLiquidity                                                   593
# removeLiquidityWithPermit                                      221
# removeLiquidityETHWithPermit                                   191
# removeLiquidityETHWithPermitSupportingFeeOnTransferTokens       68
# removeLiquidityETH                                              46
# removeLiquidity                                                 31
# removeLiquidityETHSupportingFeeOnTransferTokens                  3

# weired_tx: 0xc24c95685f2fcd22814e9c132a3ef08503d3723449af080b5edfefbdeb25e51c

# %%
# get logs (pair_logs has four pairs so it is a bit slower)
with LogsGetter() as logs_getter:
    mvs_logs = logs_getter.get_token_logs('multiverse', mvs)
    pair_logs = logs_getter.get_pair_logs('multiverse', pair_addrs)
# %%
pair_logs_dict = {}
pair_tokens = [
    busd_addr.lower(),
    bsc_usd_addr.lower(), '0xba2ae424d960c26247dd6c32edc70b295c744c43'.lower(),
    wbnb_addr.lower()
]
pair_logs_dict2 = {}
for i, hash in enumerate(pair_addrs):
    pair_logs_dict[hash] = pair_logs[i]
    pair_logs_dict2[pair_tokens[i]] = pair_logs[i]
# %%
with TxsGetter() as txs_getter:
    router_txs = txs_getter.all_txs(datetime.date(2021, 12, 30))

# %%
mvs_transfer_logs = mvs_logs.loc[mvs_logs['topic0'].map(hex_to_topic_name) ==
                                 'transfer']
mvs_approve_logs = mvs_logs.loc[mvs_logs['topic0'].map(hex_to_topic_name) ==
                                'approve']
# %%
mvs_logs['topic2'].value_counts()

# %%
pd.concat([mvs_transfer_logs['topic1'], mvs_transfer_logs['topic2']
           ]).value_counts().index.map(lambda x: '0x' + x[26:66])
# %%
# historical holders
transfer_cnt = mvs_transfer_logs['topic2'].value_counts()

with TxsGetter() as txs_getter:
    historical_holders, mvs_txs = txs_getter.get_txs_and_external_accounts_holders(
        token_logs=mvs_logs,
        pair_logs=pair_logs,
        holders=transfer_cnt.index.to_series().map(lambda x: '0x' + x[26:66]),
        start_date=datetime.date(2021, 12, 24),
        end_date=datetime.date(2022, 1, 29))
# %%
addr_topic = transfer_cnt.loc[transfer_cnt > 5 & transfer_cnt.index.to_series(
).isin(historical_holders)].index.to_series().sample(1).iloc[0]

addr = '0x' + addr_topic[26:66]
# %%
addr = '0x22168bd61e83228471098645aad1beb1269221d6'
addr_topic = '0x' + '0' * 24 + addr[2:]
# %%
print(len(historical_holders))
print(addr_topic)
print(addr)
# %%
mvs_approve_logs.loc[mvs_approve_logs['topic1'] == addr_topic,
                     'topic2'].value_counts()
# %%
# only useful thing in approval should be the spender
mvs_approve_logs.loc[mvs_approve_logs['topic1'] == addr_topic,
                     'transactionHash'].iloc[0]
# %%
# approve_logs is empty, trace the transfer_logs
addr_transfer_logs = mvs_transfer_logs.loc[
    (mvs_transfer_logs['topic1'] == addr_topic) |
    (mvs_transfer_logs['topic2'] == addr_topic), ]
# %%
addr_transfer_logs
# %%
len(addr_transfer_logs)

# %%
addr_txs = mvs_txs.loc[mvs_txs['from'] == addr]
# %%
addr_txs
# %%
len(addr_txs)

# %%
# useless
addr_pair_logs = pd.concat([
    logs.loc[(logs['topic1'] == addr_topic) | (logs['topic2'] == addr_topic)]
    for logs in pair_logs
])

# %%
set(addr_txs.index).issubset(set(addr_transfer_logs['transactionHash']))
# %%
addr_approve_logs = mvs_approve_logs.loc[mvs_approve_logs['topic1'] ==
                                         addr_topic, 'topic2']
if addr_approve_logs.empty:
    pass
elif addr_approve_logs.iloc[
        0] == pancake_router_topic and addr_approve_logs.nunique() == 1:
    addr_transfer_logs = mvs_transfer_logs.loc[
        (mvs_transfer_logs['topic1'] == addr_topic) |
        (mvs_transfer_logs['topic2'] == addr_topic), ]

    addr_txs = mvs_txs.loc[mvs_txs['from'] == addr]

    if len(addr_txs) == len(addr_transfer_logs):
        pass
else:
    pass
# %%
addr_txs['input'].map(lambda x: router_input_decoder.decode(x)[0])

# %%
balance = {
    'account': addr,
    mvs: 0,
    'mvs_transfer_in': 0,
    busd_addr.lower(): 0,
    bsc_usd_addr.lower(): 0,
    '0xba2ae424d960c26247dd6c32edc70b295c744c43': 0,
    wbnb_addr.lower(): 0
}
# %%
if addr_txs.index.to_series().isin(
        addr_transfer_logs['transactionHash']).all():
    for _, log in addr_transfer_logs.iterrows():
        if log['transactionHash'] in addr_txs.index:
            tx = addr_txs.loc[log['transactionHash']]

            method_name, input_data = router_input_decoder.decode(tx['input'])

            path = input_data['path']

            if path[-1] == mvs.lower():
                pair_token = path[-2]
            elif path[0] == mvs.lower():
                pair_token = path[1]
            else:
                print('Warning: pair not match!!!')
                break

            pair_log = pair_logs_dict2[pair_token]

            swap_data = pair_log.loc[(pair_log['transactionHash'] == tx.name)
                                     & (pair_log['topic0'] == swap_topic),
                                     'data'].values

            # TODO: this conditions should be ensured
            if input_data['to'] != addr:
                print("Warning! the receiver of the swap is someone else!")
            if len(swap_data) != 1:
                print('Warning! ')

            amount0In, amount1In, amount0Out, amount1Out = (int(
                swap_data[0][2 + 64 * i:2 + 64 * (i + 1)], 16)
                                                            for i in range(4))

            # print(amount0In, amount1In, amount0Out, amount1Out)

            balance[mvs] += amount0Out - amount0In
            balance[pair_token] += amount1Out - amount1In
        else:
            if log['topic1'] == addr_topic:
                balance['mvs_transfer_in'] -= int(log['data'], 16)
            if log['topic2'] == addr_topic:
                balance['mvs_transfer_in'] += int(log['data'], 16)
else:
    print("Warning! transactions on router should be in transfer logs")
# %%
balance
# %%
balance[busd_addr.lower()] / 10**18
# %%
for i, hash in enumerate(addr_transfer_logs['transactionHash']):
    print(i + 1, hash)
# %%
'0x' + addr_transfer_logs.iloc[1]['topic2'][26:66]
# %%
set(addr_transfer_logs['transactionHash']) - set(addr_txs.index)
# %%
pair_logs_hash_set = set()
for i in range(4):
    pair_logs_hash_set = pair_logs_hash_set.union(
        pair_logs[i]['transactionHash'])
# %%
# Wow, it is a nice conclusion!
set(mvs_txs.index).issubset(
    pair_logs_hash_set.intersection(set(mvs_logs['transactionHash'])))
