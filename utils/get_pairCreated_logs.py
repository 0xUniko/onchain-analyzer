#%%
from utils.bsc_client import w3, Scanner
from utils.pancake_utils import pancake_factory_address, pairCreated_topic, wbnb_topic
import datetime, os, time
import pandas as pd


# %%
def get_pairCreated_logs_by_timestamp(start, end, scan):
    start_block_no = int(
        scan('block', 'getblocknobytime', timestamp=start, closest='after'))
    end_block_no = int(
        scan('block', 'getblocknobytime', timestamp=end,
             closest='before')) if end < time.time() else w3.eth.block_number

    logs = []
    length = 1000

    while length == 1000:
        print('start_block_no:', start_block_no)
        print('end_block_no:', end_block_no)

        new_logs = scan('logs',
                        'getLogs',
                        fromBlock=start_block_no,
                        toBlock=end_block_no,
                        address=pancake_factory_address,
                        topic0=pairCreated_topic,
                        topic1_2_opr='or',
                        topic1=wbnb_topic,
                        topic2=wbnb_topic)

        new_logs = list(
            map(
                lambda x: {
                    'address': x['address'],
                    'topic0': x['topics'][0],
                    'topic1': x['topics'][1],
                    'topic2': x['topics'][2],
                    'data': x['data'],
                    'blockNumber': int(x['blockNumber'], 16),
                    'timeStamp': int(x['timeStamp'], 16),
                    'gasPrice': int(x['gasPrice'], 16),
                    'logIndex': int(x['logIndex'], 16),
                    'transactionHash': x['transactionHash'],
                    'transactionIndex': int(x['transactionIndex'], 16)
                }, new_logs))

        length = len(new_logs)
        if length > 0:
            start_block_no = new_logs[-1]['blockNumber']

        logs.extend(new_logs)

        time.sleep(0.21)

    return logs


# %%
def get_pairCreated_logs(date: datetime.date):
    csv = os.getcwd() + '/utils/pairCreated_logs/' + str(date) + '.csv'

    start_timestamp_of_date = int(
        time.mktime(time.strptime(str(date), '%Y-%m-%d')))
    end_timestamp_of_date = int(
        time.mktime(
            time.strptime(str(date + datetime.timedelta(days=1)),
                          '%Y-%m-%d'))) - 1

    with Scanner() as scanner:
        if os.path.exists(csv):
            logs = pd.read_csv(csv)

            update_logs = get_pairCreated_logs_by_timestamp(
                logs.iloc[-1]['timeStamp'] + 1, end_timestamp_of_date,
                scanner.scan)

            if len(update_logs) > 0:
                logs = pd.concat([logs, pd.DataFrame(update_logs)])
                logs.to_csv(csv, index=False)

            return logs
        else:
            logs = get_pairCreated_logs_by_timestamp(start_timestamp_of_date,
                                                     end_timestamp_of_date,
                                                     scanner.scan)

            logs = pd.DataFrame(logs)
            logs.to_csv(csv, index=False)

            return logs
