from .bsc_client import w3, Scanner
import json

pancake_factory_address = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'
pancake_router_address = '0x10ed43c718714eb63d5aa57b78b54704e256024e'
wbnb_addr = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
busd_addr = '0xe9e7cea3dedca5984780bafc599bd69add087d56'

wbnb_topic = '0x000000000000000000000000bb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'
busd_topic = '0x000000000000000000000000e9e7cea3dedca5984780bafc599bd69add087d56'
bscusd_topic = '0x00000000000000000000000055d398326f99059ff775485246999027b3197955'
doge_topic = '0x000000000000000000000000ba2ae424d960c26247dd6c32edc70b295c744c43'
pancake_router_topic = '0x00000000000000000000000010ed43c718714eb63d5aa57b78b54704e256024e'

pairCreated_topic = w3.keccak(
    text='PairCreated(address,address,address,uint256)').hex()
mint_topic = w3.keccak(text='Mint(address,uint256,uint256)').hex()
burn_topic = w3.keccak(text='Burn(address,uint256,uint256,address)').hex()
swap_topic = w3.keccak(
    text='Swap(address,uint256,uint256,uint256,uint256,address)').hex()
sync_topic = w3.keccak(text='Sync(uint112,uint112)').hex()
approval_topic = w3.keccak(text='Approval(address,address,uint256)').hex()
transfer_topic = w3.keccak(text='Transfer(address,address,uint256)').hex()


def hex_to_topic_name(topic: str):
    if topic == mint_topic:
        return 'mint'
    if topic == burn_topic:
        return 'burn'
    if topic == swap_topic:
        return 'swap'
    if topic == sync_topic:
        return 'sync'
    if topic == approval_topic:
        return 'approve'
    if topic == transfer_topic:
        return 'transfer'


def decode_transfer_event(topics, data):
    return {
        'from': '0x' + topics[1][26:],
        'to': '0x' + topics[2][26:],
        'value': int(data, 16)
    }


def decode_swap_event(topics, data):
    return {
        'sender': '0x' + topics[1][26:],
        'to': '0x' + topics[2][26:],
        'amount0In': int(data[2:68], 16),
        'amount1In': int(data[68:130], 16),
        'amount0Out': int(data[130:194], 16),
        'amount1Out': int(data[194:], 16)
    }


with Scanner(proxies='http://127.0.0.1:10809') as scanner:
    router_abi = scanner.scan('contract',
                              'getabi',
                              address=pancake_router_address)
pancake_router_contract = w3.eth.contract(
    address=w3.toChecksumAddress(pancake_router_address), abi=router_abi)
router_abi = json.loads(router_abi)

from eth_utils import function_abi_to_4byte_selector
from eth_utils.hexadecimal import encode_hex
from web3._utils.encoding import to_4byte_hex
from web3._utils.abi import get_abi_input_names, get_abi_input_types, map_abi_data
from web3._utils.normalizers import BASE_RETURN_NORMALIZERS
from web3 import Web3

from typing import cast
from hexbytes import HexBytes


def decode_function_input(abi, data):
    '''
    This function is used to bypass a bug in Modin when using Contract.decode_function_input of web3py
    '''
    data = HexBytes(data)  # type: ignore
    selector, params = data[:4], data[4:]

    def callable_check(fn_abi) -> bool:
        return encode_hex(
            function_abi_to_4byte_selector(fn_abi)) == to_4byte_hex(selector)

    fns_abi = [x for x in abi if x['type'] == 'function']

    func_abi = [fn_abi for fn_abi in fns_abi if callable_check(fn_abi)][0]

    names = get_abi_input_names(func_abi)
    types = get_abi_input_types(func_abi)

    decoded = Web3().codec.decode_abi(types, cast(HexBytes, params))
    normalized = map_abi_data(BASE_RETURN_NORMALIZERS, types, decoded)

    return func_abi['name'], dict(zip(names, normalized))
