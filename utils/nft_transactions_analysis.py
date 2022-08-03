from utils.Scanner import w3
from utils.CompleteGetter import CompleteGetter
from utils.seaport_utils import OrderFulfilled_event_sig, OrderFulfilledEvent, seaport_addr
from utils.x2y2_utils import EvInventoryEvent, x2y2_contract, get_x2y2_tx_balance, x2y2_addr
from eth_typing.encoding import HexStr
from eth_typing.evm import HexAddress, Address
from web3.types import TxReceipt
import pandas as pd
import datetime, time
from tqdm import tqdm
from tenacity import retry
from tenacity.wait import wait_random
from tenacity.stop import stop_after_attempt
from typing import cast, TypedDict, List

looksrare_addr = cast(HexAddress, '0x59728544B08AB483533076417FbBB2fD0B17CE3a')


def get_OrderFulfilled_balance(account: HexAddress, receipt: TxReceipt,
                               hash: HexStr, token_name: str, timeStamp: int):
    OrderFulfilled_events = [
        OrderFulfilledEvent(log['topics'], log['data'])
        for log in receipt['logs']
        if log['topics'][0] == OrderFulfilled_event_sig
    ]

    return pd.DataFrame([{
        **b.get_deal_balance(account),
        'nft_name':
        token_name,
        'time':
        datetime.datetime.fromtimestamp(timeStamp).strftime(
            '%Y-%m-%d %H:%M:%S'),
        'tx_hash':
        hash,
    } for b in OrderFulfilled_events
                         if b.offerer == account or b.recipient == account])


def get_EvInventory_balance(account: HexAddress, receipt: TxReceipt,
                            hash: HexStr, token_name: str, timeStamp: int):
    ev_inventory_events = [
        EvInventoryEvent(r['args'])
        for r in x2y2_contract.events.EvInventory().processReceipt(receipt)
    ]

    ev_profit_events = x2y2_contract.events.EvProfit().processReceipt(receipt)
    assert len(ev_profit_events) == len(
        ev_inventory_events
    ), 'ev_profit_events do not match with ev_inventory_events'

    return pd.DataFrame([{
        **get_x2y2_tx_balance(b, [
            r['args'] for r in ev_profit_events if r['args']['itemHash'] == b.detail['itemHash']
        ][0], account),
        'nft_name':
        token_name,
        'time':
        datetime.datetime.fromtimestamp(timeStamp).strftime(
            '%Y-%m-%d %H:%M:%S'),
        'tx_hash':
        hash,
    } for b in ev_inventory_events])


@retry(stop=stop_after_attempt(3),
       wait=wait_random(min=1, max=1.5),
       reraise=True)
def account_nft_transactions(account: HexAddress | Address):
    if isinstance(account, bytes):
        account = cast(HexAddress, account.hex().lower())
    else:
        account = cast(HexAddress, account.lower())

    result = pd.DataFrame([])
    for _ in range(3):
        with CompleteGetter() as getter:
            nft_transfers = getter.get_all(account, 'tokennfttx')

        if nft_transfers.empty:
            time.sleep(1.5)
            continue
        else:
            nft_transfers_in_30days = nft_transfers.loc[nft_transfers[
                'timeStamp'].map(lambda x: datetime.date.fromtimestamp(int(
                    x)) > datetime.date.today() - datetime.timedelta(days=30))]

            print('get account nft balances')
            balances = []
            for hash in tqdm(
                    nft_transfers_in_30days['hash'].drop_duplicates()):

                receipt = w3.eth.get_transaction_receipt(hash)

                if receipt['to'] == seaport_addr or receipt[
                        'to'] == x2y2_addr or receipt['to'] == looksrare_addr:

                    assert cast(
                        pd.DataFrame, nft_transfers_in_30days.loc[
                            nft_transfers_in_30days['hash'] == hash,
                            'tokenName']).nunique(
                            ) == 1, 'more than one nft collection is traded'

                    tokenName, timeStamp = nft_transfers_in_30days.loc[
                        nft_transfers_in_30days['hash'] == hash].iloc[0][[
                            'tokenName', 'timeStamp'
                        ]]

                    balances.append(
                        get_OrderFulfilled_balance(account, receipt, hash,
                                                   tokenName, int(timeStamp)))

                    balances.append(
                        get_EvInventory_balance(account, receipt, hash,
                                                tokenName, int(timeStamp)))

        result = pd.concat(balances, ignore_index=True)
        break
    return result