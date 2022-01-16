from .bsc_client import w3, Scanner

pancake_factory_address = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'
pairCreated_topic = w3.keccak(
    text='PairCreated(address,address,address,uint256)').hex()
wbnb_addr = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
wbnb_topic = '0x000000000000000000000000bb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'

pancake_router_address = '0x10ed43c718714eb63d5aa57b78b54704e256024e'
pancake_router_topic = '0x00000000000000000000000010ed43c718714eb63d5aa57b78b54704e256024e'
with Scanner() as scanner:
    router_abi = scanner.scan('contract',
                              'getabi',
                              address=pancake_router_address)
pancake_router_contract = w3.eth.contract(
    address=w3.toChecksumAddress(pancake_router_address), abi=router_abi)
