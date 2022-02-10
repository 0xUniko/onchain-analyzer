# %%
import datetime, time
from numpy import sort
import pandas as pd
import networkx as nx
from tqdm import tqdm

from utils.bsc_client import Scanner, w3
from utils.TxsGetter import TxsGetter
from utils.pancake_utils import wbnb_addr, busd_addr, bsc_usd_addr, wbnb_topic, busd_topic, bscusd_topic, pancake_router_topic, router_input_decoder
from utils.LogsGetter import LogsGetter
from utils.pancake_utils import swap_topic, hex_to_topic_name, decode_transfer_event, decode_swap_event, decode_sync_event

# %%
with LogsGetter(proxies='http://127.0.0.1:10809') as logs_getter:
    pairCreated_logs = logs_getter.get_pairCreated_logs(
        start_date=datetime.date(2021, 12, 1))

# %%
import time

print(time.time())
with TxsGetter() as txs_getter:
    liquidity_txs = pd.concat([
        txs_getter.get_router_liquidity_txs(datetime.date(2022, 1, 3)),
        txs_getter.get_router_liquidity_txs(datetime.date(2022, 1, 4))
    ])
print(time.time())

# %%
add_liquidity_eth_inputs = liquidity_txs.loc[
    liquidity_txs['method_name'] == 'addLiquidityETH'].apply(
        lambda x: {
            'timeStamp': x['timeStamp'],
            **x['data']
        },
        axis=1,
        result_type='expand')

add_liquidity_busd_inputs = liquidity_txs.loc[liquidity_txs.apply(
    lambda x: x['method_name'] == 'addLiquidity' and
    (x['data']['tokenA'] == busd_addr or x['data']['tokenB'] == busd_addr),
    axis=1)].apply(lambda x: {
        'timeStamp': x['timeStamp'],
        **x['data']
    },
                   axis=1,
                   result_type='expand')


# %%
def first_add_liquidity_log(token):
    eth_log = add_liquidity_eth_inputs.loc[add_liquidity_eth_inputs['token'] ==
                                           token].sort_values('deadline')
    busd_log = add_liquidity_busd_inputs.loc[
        (add_liquidity_busd_inputs['tokenA'] == token)
        |
        (add_liquidity_busd_inputs['tokenB'] == token)].sort_values('deadline')

    if eth_log.empty:
        if busd_log.empty:
            return False
        else:
            if busd_log.iloc[0]['tokenB'] == token:
                return {
                    'busd':
                    busd_log.iloc[0]['amountAMin'] / 10**18,
                    'bnb':
                    0,
                    'transactionHash':
                    busd_log.iloc[0].name,
                    'date':
                    datetime.date.fromtimestamp(
                        int(busd_log.iloc[0]['timeStamp']))
                }
            else:
                return {
                    'busd':
                    busd_log.iloc[0]['amountBMin'] / 10**18,
                    'bnb':
                    0,
                    'transactionHash':
                    busd_log.iloc[0].name,
                    'date':
                    datetime.date.fromtimestamp(
                        int(busd_log.iloc[0]['timeStamp']))
                }
    else:
        if busd_log.empty:
            return {
                'bnb':
                eth_log.iloc[0]['amountETHMin'] / 10**18,
                'busd':
                0,
                'transactionHash':
                eth_log.iloc[0].name,
                'date':
                datetime.date.fromtimestamp(int(eth_log.iloc[0]['timeStamp']))
            }
        else:
            if eth_log.iloc[0]['timeStamp'] < busd_log.iloc[0]['timeStamp']:
                return {
                    'bnb':
                    eth_log.iloc[0]['amountETHMin'] / 10**18,
                    'busd':
                    0,
                    'transactionHash':
                    eth_log.iloc[0].name,
                    'date':
                    datetime.date.fromtimestamp(
                        int(eth_log.iloc[0]['timeStamp']))
                }
            else:
                if busd_log.iloc[0]['tokenB'] == token:
                    return {
                        'busd':
                        busd_log.iloc[0]['amountAMin'] / 10**18,
                        'bnb':
                        0,
                        'transactionHash':
                        busd_log.iloc[0].name,
                        'date':
                        datetime.date.fromtimestamp(
                            int(busd_log.iloc[0]['timeStamp']))
                    }
                else:
                    return {
                        'busd':
                        busd_log.iloc[0]['amountBMin'] / 10**18,
                        'bnb':
                        0,
                        'transactionHash':
                        busd_log.iloc[0].name,
                        'date':
                        datetime.date.fromtimestamp(
                            int(busd_log.iloc[0]['timeStamp']))
                    }


# %%
pairCreated_logs_date = pairCreated_logs.loc[pairCreated_logs['timeStamp'].map(
    lambda x: datetime.date.fromtimestamp(x)) == datetime.date(2022, 1, 3)]

created_tokens_count_date = pd.concat(
    [pairCreated_logs_date['topic1'],
     pairCreated_logs_date['topic2']]).value_counts()

created_tokens_date = created_tokens_count_date.loc[
    created_tokens_count_date < 10].index.to_series().reset_index(
        drop=True).map(lambda x: '0x' + x[26:66])
# %%
tokens_with_liquidity = created_tokens_date.loc[
    created_tokens_date.map(first_add_liquidity_log) != False]

# %%
initial_liquidities = tokens_with_liquidity.to_frame().apply(
    lambda x: {
        'token': x[0],
        **first_add_liquidity_log(x[0])
    },
    axis=1,
    result_type='expand')
# %%
initial_liquidities.loc[initial_liquidities['bnb'] > 1].to_csv(
    'initial_liquidity0103.csv')
# %%
# %%
# CONCLUSION1: paired tokens
'''
0x000000000000000000000000bb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c (wbnb)    140155
0x000000000000000000000000e9e7cea3dedca5984780bafc599bd69add087d56 (busd)      5640
0x00000000000000000000000055d398326f99059ff775485246999027b3197955 (bsc-usd)   3417
0x0000000000000000000000000e09fabb73bd3ade0a17ecc321fd13a19e81ce82 (cake)       531
0x0000000000000000000000008ac76a51cc950d9822d68b83fe1ad97b32cd580d (usdc)       156
0x0000000000000000000000002170ed0880ac9a755fd29b2688956bd959f933f8 (bsc-eth)    144
0x0000000000000000000000007130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c (bsc-btc)    119
0x000000000000000000000000c9882def23bc42d53895b8361d0b1edc7570bc6a (fist)        79
0x000000000000000000000000ba2ae424d960c26247dd6c32edc70b295c744c43 (bsc-doge)    53
0x000000000000000000000000c748673057861a797275cd8a068abb95a902e8de (babydoge)    53
0x0000000000000000000000000cf8e180350253271f4b917ccfb0accc4862f262 (btcbr)       47
0x0000000000000000000000002859e4544c4bb03966803b044a93563bd2d0dd4d (bsc-shib)    44
0x0000000000000000000000001af3f329e8be154074d8769d1ffa4ee058b1dbc3 (bsc-dai)     40
0x000000000000000000000000641ec142e67ab213539815f67e4276975c2f8d50 (doge-king)   35
0x000000000000000000000000ee67a6ab9adfbf5c4f9fcd109c0df0462e9ecadc (bobi)        34
0x0000000000000000000000003ee2200efb3400fabb9aacf31297cbdd1d435d47 (bsc-ada)     27
0x000000000000000000000000ade6dd2f7d3b45e726f74bb50b65bef86b2f5b17 (mham)        24
0x00000000000000000000000041cf3e9534156405a133cda545af9ff0e586500a (GamingShiba) 24
0x0000000000000000000000002b3f34e9d4b127797ce6244ea341a83733ddd6e4 (floki)       24
0x0000000000000000000000003f1d29b611c649eec1e62be2237891dd88e1afe0 (serve)       23
'''
pd.concat([pairCreated_logs['topic1'],
           pairCreated_logs['topic2']]).value_counts().head(20)
# %%
# CONCLUSION2: some tokens paired to busd do not have wbnb pair, but tokens paired to bsc-usd all have wbnb or busd pair
busd_token = pairCreated_logs.loc[
    (pairCreated_logs['topic1'] == busd_topic)
    | (pairCreated_logs['topic2'] == busd_topic)].apply(
        lambda x: x['topic2'] if x['topic1'] == busd_topic else x['topic1'],
        axis=1)

wbnb_token = pairCreated_logs.loc[
    (pairCreated_logs['topic1'] == wbnb_topic)
    | (pairCreated_logs['topic2'] == wbnb_topic)].apply(
        lambda x: x['topic2'] if x['topic1'] == busd_topic else x['topic1'],
        axis=1)

print(busd_token.isin(wbnb_token).value_counts())

bscusd_token = pairCreated_logs.loc[
    (pairCreated_logs['topic1'] == bscusd_topic) |
    (pairCreated_logs['topic2'] == bscusd_topic)].apply(
        lambda x: x['topic2'] if x['topic1'] == busd_topic else x['topic1'],
        axis=1)

print(
    bscusd_token.isin(set(bscusd_token).union(set(wbnb_token))).value_counts())
# %%
