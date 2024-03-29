from typing import Literal
from ..Scanner import w3, Scanner
import json

pancake_factory_address = "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73".lower()
pancake_router_address = "0x10ed43c718714eb63d5aa57b78b54704e256024e"
wbnb_addr = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c".lower()
busd_addr = "0xe9e7cea3dedca5984780bafc599bd69add087d56"
bsc_usd_addr = "0x55d398326f99059fF775485246999027B3197955"
dai_addr = "0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3".lower()
doge_addr = "0xba2ae424d960c26247dd6c32edc70b295c744c43"
bnb_busd_pair_addr = "0x58F876857a02D6762E0101bb5C46A8c1ED44Dc16".lower()

wbnb_topic = "0x000000000000000000000000bb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
busd_topic = "0x000000000000000000000000e9e7cea3dedca5984780bafc599bd69add087d56"
bscusd_topic = "0x00000000000000000000000055d398326f99059ff775485246999027b3197955"
doge_topic = "0x000000000000000000000000ba2ae424d960c26247dd6c32edc70b295c744c43"
pancake_router_topic = (
    "0x00000000000000000000000010ed43c718714eb63d5aa57b78b54704e256024e"
)

pairCreated_topic = w3.keccak(text="PairCreated(address,address,address,uint256)").hex()
mint_topic = w3.keccak(text="Mint(address,uint256,uint256)").hex()
burn_topic = w3.keccak(text="Burn(address,uint256,uint256,address)").hex()
swap_topic = w3.keccak(
    text="Swap(address,uint256,uint256,uint256,uint256,address)"
).hex()
sync_topic = w3.keccak(text="Sync(uint112,uint112)").hex()
approval_topic = w3.keccak(text="Approval(address,address,uint256)").hex()
transfer_topic = w3.keccak(text="Transfer(address,address,uint256)").hex()
deposit_topic = w3.keccak(text="Deposit(address,uint256)").hex()
withdrawal_topic = w3.keccak(text="Withdrawal(address,uint256)").hex()


def hex_to_topic_name(topic: str):
    if topic == mint_topic:
        return "mint"
    if topic == burn_topic:
        return "burn"
    if topic == swap_topic:
        return "swap"
    if topic == sync_topic:
        return "sync"
    if topic == approval_topic:
        return "approve"
    if topic == transfer_topic:
        return "transfer"
    if topic == deposit_topic:
        return "deposit"
    if topic == withdrawal_topic:
        return "withdrawal"


def topic_name_to_hex(
    topic_name: Literal[
        "mint", "burn", "swap", "sync", "approve", "transfer", "deposit", "withdrawal"
    ]
) -> str:
    match topic_name:
        case "mint":
            return mint_topic
        case "burn":
            return burn_topic
        case "swap":
            return swap_topic
        case "sync":
            return sync_topic
        case "approve":
            return approval_topic
        case "transfer":
            return transfer_topic
        case "deposit":
            return deposit_topic
        case "withdrawal":
            return withdrawal_topic


def decode_transfer_event(topic1, topic2, data, normalize=0):
    return {
        "from": "0x" + topic1[26:],
        "to": "0x" + topic2[26:],
        "value": int(data, 16) / 10**normalize,
    }


def decode_swap_event(topic1, topic2, data, normalize=[0, 0]):
    return {
        "sender": "0x" + topic1[26:],
        "to": "0x" + topic2[26:],
        "amount0In": int(data[2:66], 16) / 10 ** normalize[0],
        "amount1In": int(data[66:130], 16) / 10 ** normalize[1],
        "amount0Out": int(data[130:194], 16) / 10 ** normalize[0],
        "amount1Out": int(data[194:], 16) / 10 ** normalize[1],
    }


def decode_sync_event(data, normalize=[0, 0]):
    return {
        "reserve0": int(data[2:66], 16) / 10 ** normalize[0],
        "reserve1": int(data[66:], 16) / 10 ** normalize[1],
    }


def decode_mint_event(data, normalize=[0, 0]):
    return {
        "amount0": int(data[2:66], 16) / 10 ** normalize[0],
        "amount1": int(data[66:], 16) / 10 ** normalize[1],
    }


def decode_pairCreated_logs(logs):
    def get_token_and_pair(log):
        if log["topic1"] == wbnb_topic or log["topic1"] == busd_topic:
            return {
                "token": "0x" + log["topic2"][26:66],
                "pair": "0x" + log["data"][26:66],
            }
        else:
            return {
                "token": "0x" + log["topic1"][26:66],
                "pair": "0x" + log["data"][26:66],
            }

    return logs.loc[
        (logs["topic1"] == busd_topic)
        | (logs["topic1"] == wbnb_topic)
        | (logs["topic2"] == busd_topic)
        | (logs["topic2"] == wbnb_topic)
    ].apply(get_token_and_pair, axis=1, result_type="expand")


with Scanner(proxies="http://127.0.0.1:10809") as scanner:
    router_abi = scanner.scan("contract", "getabi", address=pancake_router_address)
# pancake_router_contract = w3.eth.contract(
#     address=w3.toChecksumAddress(pancake_router_address), abi=router_abi
# )
router_abi = json.loads(router_abi)
