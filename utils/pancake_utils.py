from .bsc_client import w3, Scanner

pancake_factory_address = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'
pairCreated_topic = w3.keccak(
    text='PairCreated(address,address,address,uint256)').hex()
wbnb_addr = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
busd_addr = '0xe9e7cea3dedca5984780bafc599bd69add087d56'
wbnb_topic = '0x000000000000000000000000bb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'
busd_topic = '0x000000000000000000000000e9e7cea3dedca5984780bafc599bd69add087d56'
bscusd_topic = '0x00000000000000000000000055d398326f99059ff775485246999027b3197955'
doge_topic = '0x000000000000000000000000ba2ae424d960c26247dd6c32edc70b295c744c43'

pancake_router_address = '0x10ed43c718714eb63d5aa57b78b54704e256024e'
pancake_router_topic = '0x00000000000000000000000010ed43c718714eb63d5aa57b78b54704e256024e'
with Scanner() as scanner:
    router_abi = scanner.scan('contract',
                              'getabi',
                              address=pancake_router_address)
pancake_router_contract = w3.eth.contract(
    address=w3.toChecksumAddress(pancake_router_address), abi=router_abi)
