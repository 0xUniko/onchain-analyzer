from utils.Scanner import w3
from utils.CompleteGetter import CompleteGetter
from utils.seaport_utils import OrderFulfilled_event_sig, OrderFulfilledEvent
from utils.x2y2_utils import EvInventoryEvent, x2y2_contract, get_x2y2_tx_balance
from eth_typing.encoding import HexStr
from eth_typing.evm import HexAddress, Address
import pandas as pd
import datetime, time
from tqdm import tqdm
from tenacity import retry
from tenacity.wait import wait_random
from tenacity.stop import stop_after_attempt
from typing import cast, TypedDict

# TODO: !!!!!!! multiple transfers are related to one transaction, something is replicated!!!!

Transfer = TypedDict(
    'Transfer', {
        'timeStamp': int,
        'hash': HexStr,
        'from': HexAddress,
        'contractAddress': HexAddress,
        'to': HexAddress,
        'tokenName': str
    })


def get_transfer_balance(account: HexAddress | Address, transfer: Transfer):
    if isinstance(account, bytes):
        account = cast(HexAddress, account.hex().lower())
    else:
        account = cast(HexAddress, account.lower())

    receipt = w3.eth.get_transaction_receipt(transfer['hash'])

    # process seaport trades
    OrderFulfilled_events = [
        OrderFulfilledEvent(log['topics'], log['data'])
        for log in receipt['logs']
        if log['topics'][0] == OrderFulfilled_event_sig
    ]

    order_fulfilled_balances = pd.DataFrame(
        [{
            **b.get_deal_balance(account),
            'nft_name':
            transfer['tokenName'],
            'time':
            datetime.datetime.fromtimestamp(int(
                transfer['timeStamp'])).strftime('%Y-%m-%d %H:%M:%S'),
            'tx_hash':
            transfer['hash'],
        } for b in OrderFulfilled_events
         if b.offerer == account or b.recipient == account])

    # process x2y2 trades
    ev_inventory_events = [
        EvInventoryEvent(r['args'])
        for r in x2y2_contract.events.EvInventory().processReceipt(receipt)
    ]

    ev_profit_events = x2y2_contract.events.EvProfit().processReceipt(receipt)
    assert len(ev_profit_events) == len(
        ev_inventory_events
    ), 'ev_profit_events do not match with ev_inventory_events'

    x2y2_balances = pd.DataFrame([{
        **get_x2y2_tx_balance(b, [
            r['args'] for r in ev_profit_events if r['args']['itemHash'] == b.detail['itemHash']
        ][0], account),
        'nft_name':
        transfer['tokenName'],
        'time':
        datetime.datetime.fromtimestamp(int(
            transfer['timeStamp'])).strftime('%Y-%m-%d %H:%M:%S'),
        'tx_hash':
        transfer['hash'],
    } for b in ev_inventory_events])

    return pd.concat([order_fulfilled_balances, x2y2_balances],
                     ignore_index=True)


@retry(stop=stop_after_attempt(3),
       wait=wait_random(min=1, max=1.5),
       reraise=True)
def account_nft_transactions(account: HexAddress | Address):
    result = pd.DataFrame([])
    for _ in range(3):
        with CompleteGetter() as getter:
            nft_transfers = getter.get_all(account, 'tokennfttx')

        if nft_transfers.empty:
            time.sleep(1.5)
            continue
        else:
            balances = []
            nft_transfers_in_30days = nft_transfers.loc[nft_transfers[
                'timeStamp'].map(lambda x: datetime.date.fromtimestamp(int(
                    x)) > datetime.date.today() - datetime.timedelta(days=30))]

            print('get account nft balances')
            nft_transfers_in_30days_ = [
                t for t in nft_transfers_in_30days.iterrows()
            ]
            for _, transfer in tqdm(nft_transfers_in_30days_):
                balances.append(
                    get_transfer_balance(account, cast(Transfer, transfer)))

            result = pd.concat(balances, ignore_index=True)
            break
    return result