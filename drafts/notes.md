# NOTES

## **this is my notes to analysis transactions**

the relation os transactions on router and events of token and pairs

transactions on router have two types: "liquidity" and "swap"

ATTENTION:

the from of transfer log is the owner

the sender of swap log is the function caller (**msg.sender** in the code)

## Records for multiverse

### 0xf5d8d1066b04e5412ca71bf04f11de2c238708b6

This address does not make any exchange. Just some transfer records of bnb and mvs

That is to say, **this address does not have any approve log**. In this case, we can get the balance from transfer logs only.

### 0x054d51d67935034dd1094b9e574ce46f290f4cf4

no approve, 2 transfers, 2 pcs transactions

buy twice and no selling

### 0x811f0d2408584aa02614B8a5fAf6D85BF0BF09c1

2 transfers (token to pair, pair to token), 2 pcs transactions (cake for mvs, mvs for cake, huge loss), 2 approves (1 independent, 1 on the selling transaction on pcs, all for pcs router)

so, **the detail of approve is useless**. The key should be the spender.

### 0x8d6ab2fcf5339facb0054727cc9219740d4ce752

7 transfers, 7 pcs transactions, all are corresponding, buying and selling
4 approves
4 swaps, 3 are missing since, for instance, the path is [mvs, busd, bnb], we cannot get any information of the address from the mvs_busd pair since sender = pcs router and to = bnb_busd pair

we can get the missing swap by transactionHash

so the useness of swap is to get the **exact** amount in the transaction

And this guy earns $39.553253929276245 after the 7 transactions and has no mvs left. Cool!

### 0xefdb462ffcd10a0c8ed63e1adc982a2159d351e6

0 approves, 4 transfers, 2 transactions, 2 swaps

first 2 buying mvs: corresponding to 2 transfers, 2 transactions, 2 swaps, respectively

transfer all the above mvs to 0x69f6ca7c3b54d215b6b45ad131995fbfbaa7f185, an external address

interact with 0x25b419490526318404c6f195b7bdec18b0f803bb (not open sourced) get mvs

### 0x69f6ca7c3b54d215b6b45ad131995fbfbaa7f185

8 approves for pcs router, 17 transfers, 14 transactions, 8 pair logs (all swap)

set(addr_txs.index).issubset(set(addr_transfer_logs['transactionHash'])) == True

1, 0x0dbbbf05060383530544ac534a09cbb159dae8b5 transfers 1,964,599.838852801605882273 mvs in

2, sell 983,567.136008766263188801 mvs for 3,437.668160269446541717 busd

3, sell 598,567.871565112252994592 mvs for 1,956.790041173288150764 busd

4, buy 1,254,486.330795605952790929 mvs for 4,044.103600445803921679 busd

5, buy 88,208.118976747438751449 mvs for 291.589131525239892478 busd

6, buy 220,201.155360352281406139 mvs for 728.797293953328175011 busd

7, buy 274,659.132629941670851443 mvs for 998.892987823687274484 busd

8, sell 2,220,019.56904157043349884 mvs for 2,885.939300165888808002 busd

9, buy 1,110,659.918342031076548398 mvs for 1,486.108762485169419707 busd

10, buy 369,210.840609253845754876 mvs for 482.931651726517611393 busd

11, buy 398,594.578743560704275751 mvs for 675.699972069260598555 busd

12, sell 691,178.440426843920129119 mvs for 970.310984740225364433 busd

13, 0xefdb462ffcd10a0c8ed63e1adc982a2159d351e6 transfers 206,935.128233649767993853 mvs in

14, sell 901,215.450524510137495263 mvs for 921.591403888314977416 busd

15, sell 493,006.574977141336948496 mvs for 390.385461302071799896 busd

16, 0x454eb234a7a58e0604e53e7c50ef7392de0acacb transfers 185,934.367640973561798045 mvs in

17, sell 185,934.367640973561798045 for 141.369319287465108515 busd

so, **addr_pair_logs is useless**. For a transaction that address -> pcs router -> pair -> another token -> address, no address on the pair log.

### 0x4608da04bc02f744aab0252d9c0272c6bb2ebd66

buy 518.51134910654272224 + 378.749715607669195979
sell 902.032025163980322807 + 998.94903901601352902

profit a lot! excellent!

### 0xe27d2906ad1a1d80a538f847858790b2888c6e67

1, buy 17,756.133872806194292486 for 52.206196148682400202 busd

2, buy 165,752.412604384576897323 for 484.290046056106917322 busd

3, buy 329,451.418238836272877383 for 960.02315767603122533 busd

4, transfer 512,959.964716027044067192 mvs to 0xfcfda35a51b245639493649ad13b13f29f3b4a47

5, receive 112,959.964716027044067192 mvs from 0xfcfda35a51b245639493649ad13b13f29f3b4a47

6, sell 112,959.964716027044067192 mvs for 803.141448639916469021 busd

7, buy 42,938.355180202346514407 mvs for 61.022849352816283835 busd

8, transfer 42,938.355180202346514407 mvs to 0xfcfda35a51b245639493649ad13b13f29f3b4a47

9, buy 287,962.847794615751869841 mvs for 390.647033315612872691 busd (**the length of swap path is 16!**)

10, buy 209,717.3610863046757399 mvs for 286.003016621898612868 busd

11, buy 86,891.891493318358147799 mvs for 118.068100897413573365 busd

12, transfer 584,572.10037423878575754 mvs to 0xfcfda35a51b245639493649ad13b13f29f3b4a47

### 0xf1535df3adcd75a0cd3ae93a852e07e714a53013

1, receive 100 mvs from 0xea17320a687d434623e2de88a5795b81b4648421

2, receive 110,072,837.101799999039565378  mvs from 0xea17320a687d434623e2de88a5795b81b4648421

3, receive 55,549.892515464937341416  mvs from 0xea17320a687d434623e2de88a5795b81b4648421

4, receive 11,007 mvs from 0xea17320a687d434623e2de88a5795b81b4648421

5, receive 209,969.041871692298470367 mvs from 0xea17320a687d434623e2de88a5795b81b4648421

6, sell 110,349,463.036187156275377161 mvs for 223,401.373207976615807616 busd

7, receive 550 mvs from 0x58f73970655adf76cb6094779b3937938f9931ba

8, transfer 15.0100024 mvs to 0x431E5e2975dB8A3563876eAE7D33A0864A0E8096

9, transfer 1 mvs to 0xd4BA2990E3b13C3244D3CAFf0fC35F5536f33305

10, buy 11,101 mvs for 14.295760420011562129 busd

11, transfer 11,101 for 0x431E5e2975dB8A3563876eAE7D33A0864A0E8096

12, transfer 50 mvs to 0xAc9126665BC61A962A43b1fF34669990AAE7e0D2

13, transfer 0.00002 mvs to 0x58f73970655adf76cb6094779b3937938f9931ba

14, transfer 0.010621 mvs to 0x0C3E4B4B76DFFA45da87271BB37353d84125128F

15, buy 405.0005 mvs for 0.302238214868478043 busd

16, buy 666.666 mvs for 0.497939611637990736 busd

17, transfer 666.666 mvs to 0x0C3E4B4B76DFFA45da87271BB37353d84125128F

### 0x502fbf208e37a5ee869d925384f8109422823bd0

1, receive 5,000,000,000 from 0x54d085fb94558f0073158066666aeb1c417386b0

2, addLiquidity (PairCreated)

### 0xc8d81185941174b08e66df5975b75a089a4e7060

many transactions including liquidity things

### 0x3bfb875fcb509e924842db85a8ea5ff2515b88e4

many transfer in one transaction

### 0x411cb65eeef547f440196aabbd32f0f82def553e

20211224第一天进了8426.306771715103busd之后一直到20220111-20220114出货，买在第一买在最低卖在最高

还有跟的若干转账记录（包括收益第二0x36f98cb56d7244c4597bd4f92f10a35b6fef9ded），结果是净转出

这几个账号都是一伙的：0xa3527740ebd010a16117a9e16183f150aeb7e9ec，0x36f98cb56d7244c4597bd4f92f10a35b6fef9ded

### 0xf1535df3adcd75a0cd3ae93a852e07e714a53013

主要是之前的转入：
2021-12-30 ('0xea17320a687d434623e2de88a5795b81b4648421', 100.0)
2021-12-30 ('0xea17320a687d434623e2de88a5795b81b4648421', 110072837.1018)
2022-01-01 ('0xea17320a687d434623e2de88a5795b81b4648421', 55549.89251546494)
2022-01-02 ('0xea17320a687d434623e2de88a5795b81b4648421', 11007.0)
2022-01-14 ('0xea17320a687d434623e2de88a5795b81b4648421', 209969.0418716923)

然后16号全部卖出

### 0xea17320a687d434623e2de88a5795b81b4648421

也是早早就埋伏了：
0 2021-12-24 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': 96163514.4908749, '0xe9e7cea3dedca5984780bafc599bd69add087d56': -20745.815703054996}
1 2021-12-25 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': 6843362.761017103, '0xe9e7cea3dedca5984780bafc599bd69add087d56': -5246.635735942586}
2 2021-12-28 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': 379928.78390088346, '0xe9e7cea3dedca5984780bafc599bd69add087d56': -1553.8815}
3 2021-12-29 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': 6615851.280886135, '0xe9e7cea3dedca5984780bafc599bd69add087d56': -20361.769412625355}
4 2021-12-30 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': 1116592.8696498342, '0xe9e7cea3dedca5984780bafc599bd69add087d56': -2698.08954494}

### **0xcfc4ef2d189cd57ecdcb70adf21ad6cf4a709cea**

转账记录干净，第一天冲进去了

0 2021-12-24 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': 5327581.430153841, '0xe9e7cea3dedca5984780bafc599bd69add087d56': -4530.395235108026}
1 2021-12-24 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': 120265843.56818876, '0xe9e7cea3dedca5984780bafc599bd69add087d56': -136512.8745}
2 2021-12-28 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': -20000000.0, '0xe9e7cea3dedca5984780bafc599bd69add087d56': 57792.37640377886}
3 2021-12-28 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': -20000000.0, '0xe9e7cea3dedca5984780bafc599bd69add087d56': 55289.60022314189}
4 2021-12-28 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': -10000000.0, '0xe9e7cea3dedca5984780bafc599bd69add087d56': 30774.266665269268}
5 2021-12-28 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': -20000000.0, '0xe9e7cea3dedca5984780bafc599bd69add087d56': 52073.352294842145}
6 2021-12-29 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': -5000000.0, '0xe9e7cea3dedca5984780bafc599bd69add087d56': 12598.980870751222}
7 2022-01-14 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': -20000000.0, '0xe9e7cea3dedca5984780bafc599bd69add087d56': 58462.316760175614}
8 2022-01-14 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': -20000000.0, '0xe9e7cea3dedca5984780bafc599bd69add087d56': 54067.40697900806}
9 2022-01-14 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': -10593424.998342594, '0xe9e7cea3dedca5984780bafc599bd69add087d56': 33026.77412417333}
10 2022-01-23 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': 25219417.543260742, '0xe9e7cea3dedca5984780bafc599bd69add087d56': -20089.456550751223}
11 2022-01-24 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': 2333967.1073434814, '0xe9e7cea3dedca5984780bafc599bd69add087d56': -1722.0580362446285}
12 2022-01-24 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': 4919926.058057874, '0xe9e7cea3dedca5984780bafc599bd69add087d56': -3728.987046863338}
13 2022-01-24 {'0x98Afac3b663113D29dc2Cd8C2d1d14793692F110': -100000.0, '0xe9e7cea3dedca5984780bafc599bd69add087d56': 86.73463969020011}
2022-01-24 ('0x25b419490526318404c6f195b7bdec18b0f803bb', 3015.8399966933825)

### 0xa4ca9b759e0d7882d0c8614c37f424841aa9a011

TODO:从第一天起就开始往外转与卖币？币是哪里来的？

### 0x8883484a0529e1b069078082773cf6b02252f40e

也是第一天冲进去了，后面以卖的多

### 0xa9648135150b7f9667cbb84eb960c2ba18fb0aab

第一天开始就买币卖币了，但是TODO: 好像第一天卖的币还多于买的币？？？

### 0xe4bba2c7d91641a11083c4f27e5ba248d0cbf921

check_approve == False

## richmoon的记录

持币实体数增长的那几天正好是爆拉的时间，此时前期埋伏的在出货

## Logs analysis

except for liquidity serises and swap serises, there are the following situations:

revoke lp, approve, and many other possibilities: approve pair for router

transfers

some formula (can be used to verify the correctness of data source):

1,

```python
set(mvs_txs.index).issubset(
    pair_logs_hash_set.intersection(set(mvs_logs['transactionHash']))) == True
```

mvs_txs should be calculated by TxsGetter.get_router_txs_by_token, and this formula leads to the faster method TxsGetter.get_txs_and_external_accounts_holders

2,

```python
def is_tx_hash_related_to_multi_transfer_logs(hash):
    method_name, input_data = router_input_decoder.decode(mvs_txs.loc[hash,'input'])
    return 'swap' in method_name and len(mvs_transfer_logs.loc[
        mvs_transfer_logs['transactionHash'] == hash]) > 1

mvs_txs.index.to_series().map(
    is_tx_hash_related_to_multi_transfer_logs).nunique() == 1
```

## 想法

交易量，参与交易人数，庄家（持币最多的人、曾经持有币最多的人，transfer的数量最大的人）

散户进场大户出场就是离场点

怎么判断是否进场何时进场？

池子大小，购买的人与钱，那些拿出真金白银喂给土狗的地址

筛选更多跑出来了的土狗，先用池子大小初筛看看

## process

for an addrss:

1, Check the approve logs. This indicate that what could take the tokens owned by the address away. If there is no approve logs or it only approves to pcs router, that is fine and we can go ahead.

2, Check the transfer logs and transaction logs. Calculate the balance from it's transaction logs.

TODO: 盈利人数与列表，亏钱人数与列表，每日交易量
mvs是否会多次转移：若干个购买者买了mvs之后是不是会汇聚到一个账号交易，之后是不是还会存在mvs转移的现象
liquidity相关的transaction的处理
验证：如果没有approve或者只approve了pcs router，那所有不在pcs router的transfer是不是topic1和topic2有一个一定为address
