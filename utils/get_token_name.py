from utils.Scanner import w3
from eth_typing.evm import ChecksumAddress
import json


def get_token_name(address: ChecksumAddress) -> str:

    with open('utils/general_abi.json', 'r') as f:
        general_abi = json.load(f)
    contract = w3.eth.contract(address, abi=general_abi)

    return contract.caller.name()
