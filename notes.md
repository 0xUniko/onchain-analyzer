# Notes (in Ropsten uniswapv2)

my_address = 0x9F638213287D827ef5210999787Eb04cD9E3c315

token_address = 0x95C6AF1A03E8f7C634794d5704D14510e3fdD479

router_address = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D

factory_address = 0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f

pair_address = 0x741E36fDf786b6aF032742Ee567A7FacB11398Df

weth_address = 0xc778417E063141139Fce010982780140Aa0cD5Ab

## 1, (token tx) Contract Creation / Create: xxx

NOTE: **This is the first of the erc20 transaction of scan api of my_address**

## 2, (token tx) approve for router

{
from: my_address,
to: token_addrees,
InputData: {
spender: router_address,
rawAmount: (hex)
}
}

## 3, (my tx) Add Liquidity ETH

{
from: my_address,
to: route_addrees,
InputData: {
token: token_addrees,
amouintTokenDesired: uint256,
amountTokenMin: uint256,
amountETHMin: uint256,
to: my_address
}
}

in this transaction the router will invoke factory to create pair

NOTE: **This can be found in the erc20 transaction of scan api of my_address** as follow:

{
from: my_address,
to: pair_address,
value: liquidity provided amount,
...
}

## 笔记

供应量分析
owner 可能只添加了一部分代币到池子，或者可能把一部分代币打进黑洞

那种频繁交易十几万次的是不是夹子机器人呢？

PairCreated 是在 factory，很多 events 是在 pair 里

## **NOTE**

流动性变更、交易、erc20 转账 都可以通过日志来追踪！！！

for Ownable token: OwnershipTransferred topic

### token creation

#### token logs

Transfer (
from: 0x0000000000000000000000000000000000000000000000000000000000000000,
to: my_address_topic,
tokens: {amount}
)

### before create pair

#### token logs

Approval (
tokenOwner: my_address_topic,
spender: router_address_topic,
tokens: {amount}
)

### PairCreated and addLiquidity

#### token logs

Transfer (
from: my_address_topic,
to: pair_address_topic,
tokens: {amount}
)

Approval (
tokenOwner: my_address_topic,
spender: router_address_topic,
tokens: {amount}
)

#### pair logs

Transfer (
from: 0x0000000000000000000000000000000000000000000000000000000000000000,
to: 0x0000000000000000000000000000000000000000000000000000000000000000,
value: 1000
)

Transfer (
from: 0x0000000000000000000000000000000000000000000000000000000000000000,
to: my_address_topic,
value: {amount}
)

Sync (
reserve0: {amount},
reserve1: {amount},
)

Mint (
sender: router_address_topic,
amount0: {amount},
amount1: {amount},
)

### swap

#### token logs

Transfer (
from: pair_address_topic,
to: buyer_address_topic,
tokens: {amount}
)

#### pair logs

Swap (
sender: uniswapv3_router_address_topic,
to: buyer_address_topic,
amount0In:{amount},
amount0Out: {amount},
amount1In: {amount},
amount1Out: {amount},
)

Sync (
reserve0: {amount},
reserve1: {amount},
)
