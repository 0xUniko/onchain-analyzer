from eth_typing.evm import HexAddress
from eth_typing.encoding import HexStr
from hexbytes import HexBytes
from typing import cast


def addr_trac(x: HexStr | HexBytes) -> HexAddress:
    if isinstance(x, HexBytes):
        h = x.hex()
    else:
        h = x

    return cast(HexAddress, '0x' + h[26:66])


def addr_padding(x: HexStr | HexBytes) -> HexAddress:
    if isinstance(x, HexBytes):
        h = x.hex()
    else:
        h = x

    return cast(HexAddress, '0x' + '0' * 24 + h[2:])
