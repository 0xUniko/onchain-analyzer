def addr_trac(x: str):
    return '0x' + x[26:66]


def addr_padding(x: str):
    return '0x' + '0' * 24 + x[2:]
