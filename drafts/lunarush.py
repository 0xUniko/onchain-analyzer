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
token_name = 'lunarush'

token_start_date = datetime.date(2022, 1, 2)
pairs_pair = [{
    'token1': '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c',
    'token2': '0xc275dddbd0aa7d8be23d98992a5b7819c3115917'
}, {
    'token1': '0x55d398326f99059ff775485246999027b3197955',
    'token2': '0xc275dddbd0aa7d8be23d98992a5b7819c3115917'
}, {
    'token1': '0xc275dddbd0aa7d8be23d98992a5b7819c3115917',
    'token2': '0xe9e7cea3dedca5984780bafc599bd69add087d56'
}, {
    'token1': '0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82',
    'token2': '0xc275dddbd0aa7d8be23d98992a5b7819c3115917'
}]
pair_addrs = [
    '0x66babd248c9bc3834267c7714bd89a6e32b5cd14',
    '0xd6b488565ab61dc24ed02f0067f72777947789be',
    '0xfe6e1145ced85bbd02b31b1d618567757ad345a3',
    '0xadd2b90ab10a2012fb5f04c325b71dfc24f86edd'
]
pair_tokens = [
    '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c',
    '0x55d398326f99059ff775485246999027b3197955',
    '0xe9e7cea3dedca5984780bafc599bd69add087d56',
    '0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82'
]
# %%
# get logs (pair_logs has four pairs so it is a bit slower)
with LogsGetter(proxies='http://127.0.0.1:10809') as logs_getter:
    # pairCreated_logs = logs_getter.get_pairCreated_logs(
    #     start_date=datetime.date(2021, 12, 1))

    # create_token_events = [
    #     log for _, log in pairCreated_logs.iterrows()
    #     if log['topic1'] == token_topic or log['topic2'] == token_topic
    # ]

    # token_start_date = datetime.date.fromtimestamp(
    #     create_token_events[0]['timeStamp'])

    # pairs_pair = [{
    #     'token1': '0x' + x['topic1'][26:66],
    #     'token2': '0x' + x['topic2'][26:66]
    # } for x in create_token_events]

    # pair_addrs = ['0x' + x['data'][26:66] for x in create_token_events]

    # pair_tokens = [
    #     '0x' + x['topic1'][26:66] if x['topic2'] == token_topic else '0x' +
    #     x['topic2'][26:66] for x in create_token_events
    # ]

    token_logs = logs_getter.get_token_logs(token_name, token)
    pair_logs = logs_getter.get_pair_logs(token_name, pair_addrs)

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

with TxsGetter(proxies='http://127.0.0.1:10809') as txs_getter:
    historical_holders, token_txs = txs_getter.get_txs_and_external_accounts_holders(
        token_logs=token_logs,
        pair_logs=pair_logs,
        holders=transfer_cnt.index.to_series().map(lambda x: '0x' + x[26:66]),
        start_date=token_start_date,
        end_date=datetime.date(2022, 1, 29))

# %%
token_start_date
# %%
