# %%
from eth_abi.abi import decode_abi
from eth_utils.abi import function_abi_to_4byte_selector

from web3_input_decoder.exceptions import InputDataError
from web3_input_decoder.utils import (
    get_types_names,
    hex_to_bytes,
)


# the path should be array not tuple
class InputDecoder:
    def __init__(self, abi):
        self.selector_to_type_def = {}

        for type_def in abi:
            if type_def["type"] == "function":
                selector = function_abi_to_4byte_selector(type_def)
                self.selector_to_type_def[selector] = type_def

    def decode(self, tx_input):
        tx_input = hex_to_bytes(tx_input)
        selector, args = tx_input[:4], tx_input[4:]
        if selector not in self.selector_to_type_def:
            raise InputDataError("Specified method not found in ABI")

        # type_def = selector_to_type_def[selector]["inputs"]
        func_abi = self.selector_to_type_def[selector]
        types, names = get_types_names(func_abi["inputs"])

        values = decode_abi(types, args)
        # return [(t, n, v) for t, n, v in zip(types, names, values)]
        return func_abi["name"], dict(zip(names, values))


router_input_decoder = InputDecoder(router_abi)
