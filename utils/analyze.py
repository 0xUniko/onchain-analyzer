# %%
import datetime, time
from numpy import percentile
import pandas as pd

from utils.bsc_client import Scanner, w3
from utils.TxsGetter import TxsGetter
from utils.pancake_utils import pancake_router_contract, wbnb_addr, busd_addr, bsc_usd_addr, dai_addr, doge_addr, pancake_router_topic, pancake_router_address, router_abi, router_input_decoder
from utils.LogsGetter import LogsGetter
from utils.pancake_utils import mint_topic, burn_topic, swap_topic, sync_topic, approval_topic, transfer_topic, hex_to_topic_name, decode_transfer_event, decode_swap_event, decode_sync_event

mvs = '0x98Afac3b663113D29dc2Cd8C2d1d14793692F110'.lower()
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
busd_addr_created_log = {
    'token0': mvs,
    'token1': busd_addr,
    'pair': pair_addrs[0]
}
mvs_start_date = datetime.date(2021, 12, 24)

# %%
# get logs (pair_logs has four pairs so it is a bit slower)
with LogsGetter() as logs_getter:
    mvs_logs = logs_getter.get_token_logs('multiverse', mvs)
    pair_logs = logs_getter.get_pair_logs('multiverse', pair_addrs)

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

mvs_transfer_logs = mvs_logs.loc[mvs_logs['topic0'].map(hex_to_topic_name) ==
                                 'transfer']
mvs_approve_logs = mvs_logs.loc[mvs_logs['topic0'].map(hex_to_topic_name) ==
                                'approve']

transfer_cnt = mvs_transfer_logs['topic2'].value_counts()

with TxsGetter() as txs_getter:
    historical_holders, mvs_txs = txs_getter.get_txs_and_external_accounts_holders(
        token_logs=mvs_logs,
        pair_logs=pair_logs,
        holders=transfer_cnt.index.to_series().map(lambda x: '0x' + x[26:66]),
        start_date=datetime.date(2021, 12, 24),
        end_date=datetime.date(2022, 1, 29))


# %%
def check_approve(addr):
    addr_topic = '0x' + '0' * 24 + addr[2:]
    addr_approve_topic2 = mvs_approve_logs.loc[mvs_approve_logs['topic1'] ==
                                               addr_topic, 'topic2']
    if addr_approve_topic2.nunique() == 0:
        return True
    if addr_approve_topic2.nunique(
    ) == 1 and addr_approve_topic2.values[0] == pancake_router_topic:
        return True
    return False


def decode_router_input(tx):
    method_name, input_data = router_input_decoder.decode(tx['input'])

    if 'swap' in method_name:
        path = input_data['path']

        if path[-1] == mvs.lower():
            pair_token = path[-2]
        elif path[0] == mvs.lower():
            pair_token = path[1]
        else:
            print('Warning: pair not match!!!')

        pair_log = pair_logs_dict2[pair_token]

        swap_data = pair_log.loc[(pair_log['transactionHash'] == tx.name)
                                 & (pair_log['topic0'] == swap_topic),
                                 'data'].values

        if len(swap_data) != 1:
            print('Warning! more then one pair swap in a transaction!')

        amount0In, amount1In, amount0Out, amount1Out = (int(
            swap_data[0][2 + 64 * i:2 + 64 * (i + 1)], 16) for i in range(4))

        return {
            mvs: (amount0Out - amount0In) / 10**18,
            pair_token: (amount1Out - amount1In) / 10**18,
        }


def calculate_balance(addr):
    balance = {
        'account': addr,
        mvs: 0,
        'mvs_transfer_in': 0,
        busd_addr.lower(): 0,
        bsc_usd_addr.lower(): 0,
        '0xba2ae424d960c26247dd6c32edc70b295c744c43': 0,
        wbnb_addr.lower(): 0,
        'external_approve': False,
        'liquidity_method': False
    }

    if check_approve(addr):
        addr_topic = '0x' + '0' * 24 + addr[2:]

        addr_transfer_logs = mvs_transfer_logs.loc[
            (mvs_transfer_logs['topic1'] == addr_topic) |
            (mvs_transfer_logs['topic2'] == addr_topic), ]

        addr_txs = mvs_txs.loc[mvs_txs['from'] == addr]

        for _, tx in addr_txs.iterrows():
            method_name, input_data = router_input_decoder.decode(tx['input'])

            if 'swap' in method_name:
                path = input_data['path']

                if path[-1] == mvs.lower():
                    pair_token = path[-2]
                elif path[0] == mvs.lower():
                    pair_token = path[1]
                else:
                    print('Warning: pair not match!!!')
                    break

                pair_log = pair_logs_dict2[pair_token]

                swap_data = pair_log.loc[
                    (pair_log['transactionHash'] == tx.name)
                    & (pair_log['topic0'] == swap_topic), 'data'].values

                if len(swap_data) != 1:
                    print('Warning! more then one pair swap in a transaction!')

                amount0In, amount1In, amount0Out, amount1Out = (int(
                    swap_data[0][2 + 64 * i:2 + 64 * (i + 1)],
                    16) for i in range(4))

                # print(amount0In, amount1In, amount0Out, amount1Out)

                balance[mvs] += amount0Out - amount0In
                balance[pair_token] += amount1Out - amount1In

                if input_data['to'] != addr and path[-1] == mvs.lower():
                    balance['mvs_transfer_in'] -= amount0Out - amount0In
            else:
                # TODO:
                # print("Warning! liquidity method invoked")
                balance['liquidity_method'] = True

        for hash in set(addr_transfer_logs['transactionHash']) - set(
                addr_txs.index):
            logs = addr_transfer_logs.loc[addr_transfer_logs['transactionHash']
                                          == hash]

            for _, log in logs.iterrows():
                if log['topic1'] == addr_topic:
                    balance['mvs_transfer_in'] -= int(log['data'], 16)
                if log['topic2'] == addr_topic:
                    balance['mvs_transfer_in'] += int(log['data'], 16)

    else:
        balance['external_approve'] = True

    return balance


bbb = []


def print_balance(addr):
    print('check_approve:', check_approve(addr))

    addr_topic = '0x' + '0' * 24 + addr[2:]

    addr_transfer_logs = mvs_transfer_logs.loc[
        (mvs_transfer_logs['topic1'] == addr_topic) |
        (mvs_transfer_logs['topic2'] == addr_topic), ]

    addr_txs = mvs_txs.loc[mvs_txs['from'] == addr]

    for i, (_, tx) in enumerate(addr_txs.iterrows()):

        print(i, datetime.date.fromtimestamp(int(tx['timeStamp'])),
              decode_router_input(tx))
        print(tx.name, '\n')

    hashs = set(addr_transfer_logs['transactionHash']) - set(addr_txs.index)

    for _, log in addr_transfer_logs.loc[
            addr_transfer_logs['transactionHash'].isin(hashs)].iterrows():

        value = ('0x' + log['topic1'][26:66], int(log['data'], 16) /
                 10**18) if log['topic2'] == addr_topic else (
                     '0x' + log['topic2'][26:66],
                     -int(log['data'], 16) / 10**18)
        bbb.append(value)
        print(datetime.date.fromtimestamp(log['timeStamp']), value)
        print(log['transactionHash'], '\n')


# %%
from tqdm import tqdm

balances = []

for addr in tqdm(historical_holders):
    balances.append(calculate_balance(addr))
# %%
print_balance('0xa9648135150b7f9667cbb84eb960c2ba18fb0aab')
# %%
busd_balance = balances[busd_addr].map(lambda x: int(x / 10**18))
# %%
balances.sort_values(busd_addr).tail(20)
# %%
balances = pd.read_csv('result1.csv', index_col=0)
# %%
balances[busd_addr] = balances[busd_addr].map(lambda x: int(x))
