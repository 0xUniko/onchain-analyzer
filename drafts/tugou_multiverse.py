# %%
import datetime, time
import pandas as pd

from utils.bsc_client import Scanner, w3
from utils.TxsGetter import TxsGetter
from utils.pancake_utils import pancake_router_contract, wbnb_addr, pancake_router_topic, pancake_router_address, router_abi, router_input_decoder
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
hashs = []
hashs.extend(mvs_logs['transactionHash'])
for log in pair_logs:
    hashs.extend(log['transactionHash'])
hashs = set(hashs)
print(len(hashs))
# %%
txs
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

# %%
print(len(historical_holders))
print(addr_topic)
print(addr_topic[26:66])
# %%
mvs_approve_logs.loc[mvs_approve_logs['topic1'] == addr_topic,
                     'topic2'].value_counts()
# %%
mvs_approve_logs.loc[mvs_approve_logs['topic1'] == addr_topic,
                     ['transactionHash', 'data']].iloc[1, 0]
'0x' + addr_topic[26:66]
# %%
mvs_txs.loc[mvs_txs['from'] == '0x' + addr_topic[26:66]]
# %%
addr_txs_logs = mvs_transfer_logs.loc[
    (mvs_transfer_logs['topic1'] == addr_topic) |
    (mvs_transfer_logs['topic2'] == addr_topic), ]
# %%
print(len(addr_txs_logs))

# %%