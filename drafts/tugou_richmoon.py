# %%
import datetime, time
from numpy import sort
import pandas as pd
import networkx as nx
from tqdm import tqdm

from utils.bsc_client import Scanner, w3
from utils.TxsGetter import TxsGetter
from utils.pancake_utils import wbnb_addr, busd_addr, bsc_usd_addr, pancake_router_topic, router_input_decoder
from utils.LogsGetter import LogsGetter
from utils.pancake_utils import swap_topic, hex_to_topic_name, decode_transfer_event, decode_swap_event, decode_sync_event

token = '0xC275DDdBD0AA7d8Be23D98992a5B7819c3115917'.lower()
token_topic = '0x000000000000000000000000' + token[2:].lower()
pair_tokens = [
    '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c',
    '0x55d398326f99059ff775485246999027b3197955',
    '0xe9e7cea3dedca5984780bafc599bd69add087d56'
]
pair_addrs = [
    # bnb-pair
    '0x66babd248c9bc3834267c7714bd89a6e32b5cd14',
    # bsc-usd-pair
    '0xd6b488565ab61dc24ed02f0067f72777947789be',
    # busd-pair
    '0xfe6e1145ced85bbd02b31b1d618567757ad345a3'
]
pairs_pair = [{
    'token1': '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c',
    'token2': '0xc275dddbd0aa7d8be23d98992a5b7819c3115917'
}, {
    'token1': '0x55d398326f99059ff775485246999027b3197955',
    'token2': '0xc275dddbd0aa7d8be23d98992a5b7819c3115917'
}, {
    'token1': '0xc275dddbd0aa7d8be23d98992a5b7819c3115917',
    'token2': '0xe9e7cea3dedca5984780bafc599bd69add087d56'
}]
token_start_date = datetime.date(2022, 1, 2)
# %%
# get logs (pair_logs has four pairs so it is a bit slower)
with LogsGetter() as logs_getter:
    # pairCreated_logs = logs_getter.get_pairCreated_logs(
    #     start_date=datetime.date(2021, 12, 1))

    # create_token_events = [
    #     log for _, log in pairCreated_logs.iterrows()
    #     if log['topic1'] == token_topic or log['topic2'] == token_topic
    # ]

    # pairs_pair = [{
    #     'token1': '0x' + x['topic1'][26:66],
    #     'token2': '0x' + x['topic2'][26:66]
    # } for x in create_token_events]

    # pair_addrs = ['0x' + x['data'][26:66] for x in create_token_events]
    # pair_tokens = [
    #     '0x' + x['topic1'][26:66] if x['topic2'] == token_topic else '0x' +
    #     x['topic2'][26:66] for x in create_token_events
    # ]

    token_logs = logs_getter.get_token_logs('richmoon', token)
    pair_logs = logs_getter.get_pair_logs('richmoon', pair_addrs)

pair_logs_dict = {}
for i in range(len(pair_logs)):
    pair_logs_dict[pair_tokens[i]] = pair_logs[i]

token_transfer_logs = token_logs.loc[token_logs['topic0'].map(
    hex_to_topic_name) == 'transfer']
token_approve_logs = token_logs.loc[token_logs['topic0'].map(hex_to_topic_name)
                                    == 'approve']

# token_start_date = datetime.date.fromtimestamp(
#     pair_logs[0].iloc[0]['timeStamp'])

# historical holders
transfer_cnt = token_transfer_logs['topic2'].value_counts()

with TxsGetter() as txs_getter:
    historical_holders, token_txs = txs_getter.get_txs_and_external_accounts_holders(
        token_logs=token_logs,
        pair_logs=pair_logs,
        holders=transfer_cnt.index.to_series().map(lambda x: '0x' + x[26:66]),
        start_date=token_start_date,
        end_date=datetime.date(2022, 1, 29))


# %%
def check_approve(addr):
    addr_topic = '0x' + '0' * 24 + addr[2:]
    addr_approve_topic2 = token_approve_logs.loc[
        token_approve_logs['topic1'] == addr_topic, 'topic2']
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

        if path[-1] == token.lower():
            pair_token = path[-2]
        elif path[0] == token.lower():
            pair_token = path[1]
        else:
            print('Warning: pair not match!!!')

        pair_log = pair_logs_dict[pair_token]

        swap_data = pair_log.loc[(pair_log['transactionHash'] == tx.name)
                                 & (pair_log['topic0'] == swap_topic),
                                 'data'].values

        if len(swap_data) != 1:
            print('Warning! more then one pair swap in a transaction!')

        amount0In, amount1In, amount0Out, amount1Out = (int(
            swap_data[0][2 + 64 * i:2 + 64 * (i + 1)], 16) for i in range(4))

        return {
            token: (amount1Out - amount1In) / 10**18,
            pair_token: (amount0Out - amount0In) / 10**18,
        }


def print_balance(addr):
    print('check_approve:', check_approve(addr))

    addr_topic = '0x' + '0' * 24 + addr[2:]

    addr_transfer_logs = token_transfer_logs.loc[
        (token_transfer_logs['topic1'] == addr_topic) |
        (token_transfer_logs['topic2'] == addr_topic), ]

    addr_txs = token_txs.loc[token_txs['from'] == addr]

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
        # bbb.append(value)
        print(datetime.date.fromtimestamp(log['timeStamp']), value)
        print(log['transactionHash'], '\n')


def print_entity_balance(entity):
    print('check_approve:',
          pd.Series([check_approve(addr) for addr in entity]).all())

    entity_txs = token_txs.loc[token_txs['from'].isin(entity)]

    for i, (_, tx) in enumerate(entity_txs.iterrows()):

        print(i, datetime.date.fromtimestamp(int(tx['timeStamp'])),
              decode_router_input(tx))
        print(tx.name, '\n')


def get_entity_balance(entity, transfer_logs):
    if len(entity) == 1:
        return {
            'entity':
            entity,
            'token_in':
            transfer_logs.loc[transfer_logs['topic2'].
                              map(lambda x: '0x' + x[26:66]).isin(entity),
                              'data'].map(lambda x: int(x, 16)).sum(),
            'token_out':
            transfer_logs.loc[transfer_logs['topic1'].
                              map(lambda x: '0x' + x[26:66]).isin(entity),
                              'data'].map(lambda x: int(x, 16)).sum(),
        }
    else:
        return {
            'entity':
            entity,
            'token_in':
            transfer_logs.loc[(transfer_logs['topic2'].
                               map(lambda x: '0x' + x[26:66]).isin(entity)) &
                              (~transfer_logs['topic1'].
                               map(lambda x: '0x' + x[26:66]).isin(entity)),
                              'data'].map(lambda x: int(x, 16)).sum(),
            'token_out':
            transfer_logs.loc[(transfer_logs['topic1'].
                               map(lambda x: '0x' + x[26:66]).isin(entity)) &
                              (~transfer_logs['topic2'].
                               map(lambda x: '0x' + x[26:66]).isin(entity)),
                              'data'].map(lambda x: int(x, 16)).sum(),
        }


def get_all_entities_balance(transfer_logs, historical_holders):
    G = nx.Graph()

    # for addr in historical_holders:
    for addr in transfer_logs['topic2'].map(lambda x: '0x' + x[26:66]):
        if addr in historical_holders:
            G.add_node(addr)

    for _, log in transfer_logs.iterrows():
        addr1 = '0x' + log['topic1'][26:66]
        addr2 = '0x' + log['topic2'][26:66]

        if addr1 in historical_holders and addr2 in historical_holders:
            G.add_edge(addr1, addr2)

    entities_balance = []

    for entity in tqdm(list(nx.connected_components(G))):
        entities_balance.append(get_entity_balance(entity, transfer_logs))

    entities_balance = pd.DataFrame(entities_balance).sort_values(
        'token_in', ascending=False)
    entities_balance['token_amount'] = entities_balance[
        'token_in'] - entities_balance['token_out']

    return entities_balance


def get_entities_balance_daily(transfer_logs, historical_holders):
    G = nx.Graph()

    for addr in transfer_logs['topic2'].map(lambda x: '0x' + x[26:66]):
        if addr in historical_holders:
            G.add_node(addr)

    for _, log in transfer_logs.iterrows():
        addr1 = '0x' + log['topic1'][26:66]
        addr2 = '0x' + log['topic2'][26:66]

        if addr1 in historical_holders and addr2 in historical_holders:
            G.add_edge(addr1, addr2)

    dates = sort(transfer_logs['timeStamp'].map(
        lambda x: datetime.date.fromtimestamp(x)))
    start_date = dates[0]
    end_date = dates[-1]
    daily_logs = {}
    while start_date <= end_date:
        daily_logs[str(start_date)] = transfer_logs.loc[
            transfer_logs['timeStamp'].map(
                lambda x: datetime.date.fromtimestamp(x) == start_date)]
        start_date += datetime.timedelta(days=1)

    entities_balance_in = []
    entities_balance_out = []

    for entity in tqdm(list(nx.connected_components(G))):
        start_date = dates[0]
        balance_in_daily = {'entity': entity}
        balance_out_daily = {'entity': entity}

        while start_date <= end_date:
            balance = get_entity_balance(entity, daily_logs[str(start_date)])

            # balance_daily[str(start_date)] = {
            #     'token_in': balance['token_in'],
            #     'token_out': balance['token_out']
            # }

            balance_in_daily[str(start_date)] = balance['token_in']
            balance_out_daily[str(start_date)] = balance['token_out']

            start_date += datetime.timedelta(days=1)

        entities_balance_in.append(balance_in_daily)
        entities_balance_out.append(balance_out_daily)

    entities_balance_in = pd.DataFrame(entities_balance_in)
    entities_balance_out = pd.DataFrame(entities_balance_out)
    entities_balance_value = pd.concat([
        entities_balance_in['entity'],
        (entities_balance_in.iloc[:, 1:] - entities_balance_out.iloc[:, 1:])
    ],
                                       axis=1)

    return entities_balance_in, entities_balance_out, entities_balance_value


# %%
entities_balance = get_all_entities_balance(token_transfer_logs,
                                            historical_holders)
# %%
entities_balance
# %%
entities_balance_in, entities_balance_out, entities_balance_value = get_entities_balance_daily(
    token_transfer_logs, historical_holders)
# %%
pd.set_option('display.max_columns', None)
entities_balance_value.sort_values(
    str(token_start_date), ascending=False).applymap(
        lambda x: x / 10**18 if type(x) == int else x).head(50)
# %%
entities_balance_accum = entities_balance_value.apply(lambda x: x[1:].cumsum(),
                                                      axis=1)
# %%
# should be false
(entities_balance_accum < 0).any(axis=None)
# %%
entities_balance_accum.apply(lambda x: len(x[x != 0]))
# %%
swap_records = pair_logs[0].loc[(
    pair_logs[0]['topic0'].map(hex_to_topic_name) == 'swap'
) & (pair_logs[0]['timeStamp'].map(lambda x: datetime.date.fromtimestamp(
    x
)) == token_start_date)].apply(lambda x: {
    **decode_swap_event(x['topic1'], x['topic2'], x['data']), 'transactionHash':
    x['transactionHash']
},
                               axis=1,
                               result_type='expand')
