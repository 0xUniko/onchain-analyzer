#%%
from typing import List, Optional, cast
from utils.Scanner import Scanner
from utils.get_token_name import get_token_name
from eth_typing.evm import ChecksumAddress
# from utils.pancake_utils import pancake_factory_address, pairCreated_topic
from eth_typing.evm import HexAddress
import datetime, os
import pandas as pd
from tenacity import retry
from tenacity.wait import wait_random
from tenacity.stop import stop_after_attempt


class LogsGetter():

    def __init__(self, proxies='http://127.0.0.1:10809'):
        self.proxies = proxies
        self.scanner = Scanner(proxies=proxies).__enter__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.scanner.__exit__(exc_type, exc_value, trace)
        return False

    @retry(stop=stop_after_attempt(10),
           wait=wait_random(min=1, max=1.5),
           reraise=True)
    def get_logs_by_block_interval(self, start_block: int, end_block: int,
                                   address: str, **topics_param):
        logs = []
        length = 1000

        while length == 1000:
            print('start_block_no:', start_block)
            print('end_block_no:', end_block)

            new_logs = self.scanner.scan('logs',
                                         'getLogs',
                                         fromBlock=start_block,
                                         toBlock=end_block,
                                         address=address,
                                         **topics_param)

            new_logs = list(
                map(
                    lambda x: {
                        'address':
                        x['address'],
                        'topic0':
                        x['topics'][0],
                        'topic1':
                        x['topics'][1] if len(x['topics']) > 1 else None,
                        'topic2':
                        x['topics'][2] if len(x['topics']) > 2 else None,
                        'topic3':
                        x['topics'][3] if len(x['topics']) > 3 else None,
                        'data':
                        x['data'],
                        'blockNumber':
                        int(x['blockNumber'], 16),
                        'timeStamp':
                        int(x['timeStamp'], 16),
                        'gasPrice':
                        int(x['gasPrice'], 16),
                        'logIndex':
                        int(x['logIndex'], 16) if x['logIndex'] != '0x' else 0,
                        'transactionHash':
                        x['transactionHash'],
                        'transactionIndex':
                        int(x['transactionIndex'], 16)
                        if x['transactionIndex'] != '0x' else 0
                    }, new_logs))

            logs = [log for log in logs if log['blockNumber'] != start_block]

            logs.extend(new_logs)

            length = len(new_logs)

            if length > 0:
                start_block = new_logs[-1]['blockNumber']

        return logs

    def get_logs(self, name: str, address: HexAddress, date: datetime.date,
                 **topics_param) -> pd.DataFrame:
        dirname = os.path.join('utils', name)

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        filename = os.path.join('utils', name, f'{str(date)}.csv')

        if os.path.exists(filename):

            logs = pd.read_csv(filename, index_col=0)

            last_log = sorted([
                f for f in os.listdir(dirname)
                if len(f) == 14 and f[-3:] == 'csv'
            ])[-1][:10]

            if str(date) == last_log:
                start_block, end_block = Scanner.get_start_end_block_of_date(
                    date, proxies=self.proxies)

                if not logs.empty:
                    start_block = logs.iloc[-1]['blockNumber']

                new_logs = self.get_logs_by_block_interval(
                    start_block, end_block, address, **topics_param)

                if not logs.empty:
                    new_logs = [
                        log for log in new_logs if log['transactionHash']
                        not in logs['transactionHash'].values
                    ]

                logs = pd.concat([logs, pd.DataFrame(new_logs)],
                                 ignore_index=True)

                if new_logs:
                    logs.to_csv(filename)
        else:
            start_block, end_block = Scanner.get_start_end_block_of_date(
                date, proxies=self.proxies)

            logs = self.get_logs_by_block_interval(start_block, end_block,
                                                   address, **topics_param)

            logs = pd.DataFrame(logs)

            logs.to_csv(filename)

        return logs

    def get_all_logs(self, name: str, address: HexAddress,
                     start_date: datetime.date,
                     **topics_param) -> pd.DataFrame:
        date = start_date
        today = datetime.date.today()
        logs = []

        while not date > today:
            logs.append(self.get_logs(name, address, date, **topics_param))

            date += datetime.timedelta(days=1)

        return pd.concat(logs, ignore_index=True)

    def get_token_logs(
        self,
        token_addr: HexAddress,
        token_name: Optional[str] = None,
    ) -> pd.DataFrame:
        start_timestamp_hex = self.scanner.scan(
            'logs', 'getLogs', address=token_addr)[0]['timeStamp']

        start_date = datetime.date.fromtimestamp(int(start_timestamp_hex, 16))

        if token_name is None:
            token_chechsum_addr = cast(ChecksumAddress, token_addr)
            token_name = get_token_name(token_chechsum_addr)

        return self.get_all_logs(token_name, token_addr, start_date)

    def get_pair_logs(
        self,
        token_name: str,
        token_addrs: List[HexAddress],
    ) -> List[pd.DataFrame]:
        return [
            self.get_token_logs(
                token,
                os.path.join(token_name, f'pair{i}'),
            ) for i, token in enumerate(token_addrs)
        ]

    # def get_pairCreated_logs(
    #     self,
    #     start_date=datetime.date.today() - datetime.timedelta(days=30),
    # ) -> pd.DataFrame:

    #     return self.get_all_logs('pairCreated_logs',
    #                              pancake_factory_address,
    #                              start_date,
    #                              topic0=pairCreated_topic)
