# NOTES

## **this is my notes to analysis transactions**

the relation os transactions on router and events of token and pairs

transactions on router have two types: "liquidity" and "swap"

both are related to event on pair

what's the relation to holder?

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

### 0xe4bba2c7d91641a11083c4f27e5ba248d0cbf921

## Logs analysis

except for liquidity serises and swap serises, there are the following situations:

revoke lp, approve, and many other possibilities: approve pair for router

transfers

a cool relationship is:

set(mvs_txs.index).issubset(
    pair_logs_hash_set.intersection(set(mvs_logs['transactionHash']))) == True

## process

for an addrss:

1, Check the approve logs. This indicate that what could take the tokens owned by the address away. If there is no approve logs or it only approves to pcs router, that is fine and we can go ahead.

2, Check the transfer logs and transaction logs. Calculate the balance from it's transaction logs.

TODO: 盈利人数与列表，亏钱人数与列表，每日交易量
mvs是否会多次转移：若干个购买者买了mvs之后是不是会汇聚到一个账号交易，之后是不是还会存在mvs转移的现象
liquidity相关的transaction的处理
