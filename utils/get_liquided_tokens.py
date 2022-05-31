#%%
from re import S
from utils.Scanner import Scanner
from utils.pancake_utils import wbnb_topic, wbnb_addr
from utils.get_pairCreated_logs import get_pairCreated_logs
from tenacity import Retrying, stop_after_attempt, wait_random
import datetime, json, os, asyncio


# %%
async def get_txs(index, event, length, scanner, semaphore):
    lp_addr = '0x' + event['data'][26:66]
    token = ('0x' +
             event['topic1'][26:66]) if event['topic0'] != wbnb_topic else (
                 '0x' + event['topic2'][2][26:66])

    try:
        for attemp in Retrying(stop=stop_after_attempt(100),
                               wait=wait_random(min=1, max=1.5)):
            with attemp:
                async with semaphore:
                    token_tx_list = await scanner.scan_async(
                        'account',
                        'tokentx',
                        contractaddress=token,
                        address=lp_addr)
                    bnb_tx_list = await scanner.scan_async(
                        'account',
                        'tokentx',
                        contractaddress=wbnb_addr,
                        address=lp_addr)

                if len(
                        token_tx_list
                ) >= 500 * (length - index) / length + 50 or len(
                        bnb_tx_list) >= 500 * (length - index) / length + 50:
                    print(index, '    ', token)
                    return token, 'token'

    except Exception as e:
        print(index, '      ', e)
        return token, 'error'
    finally:
        # The gap time here is not for 5 request. Is it for the 2 request in get_txs only? The gap time can be shorter.
        await asyncio.sleep(1.2)


async def get_liquided_tokens(date: datetime.date):
    async with Scanner() as scanner:
        logs = get_pairCreated_logs(date)

        semaphore = asyncio.Semaphore(5)

        result = await asyncio.gather(*[
            get_txs(index, event, len(logs), scanner, semaphore)
            for index, event in logs.iterrows()
        ])

        tokens = list(filter(lambda x: x != None, result))

        with open(
                os.getcwd() + '/utils/filtered_tokens/' +
                date.strftime('%Y%m%d') + '.json', 'w') as f:
            f.write(
                json.dumps({
                    'tokens':
                    list(filter(lambda x: x[1] == 'token'), tokens),
                    'errors':
                    list(filter(lambda x: x[1] == 'error'), tokens)
                }))


# %%
if __name__ == '__main__':
    asyncio.run(get_liquided_tokens, datetime.date(2022, 1, 12))