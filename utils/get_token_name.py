from utils.Scanner import w3
from eth_typing.evm import ChecksumAddress
import json


def get_token_name(address: ChecksumAddress) -> str:

    with open('utils/general_abi.json', 'r') as f:
        general_abi = json.load(f)
    contract = w3.eth.contract(address, abi=general_abi)

    return contract.caller.name()


def get_token_name_cached(address: ChecksumAddress) -> str:
    with open('utils/token_names.json', 'r') as f:
        token_names = json.load(f)

    if address in token_names:
        return token_names[address]
    else:
        with open('utils/general_abi.json', 'r') as f:
            general_abi = json.load(f)
        contract = w3.eth.contract(address, abi=general_abi)

        name = contract.caller.name()
        token_names[address] = name

        with open('utils/token_names.json', 'w') as f:
            json.dump(token_names, f)

        return name
