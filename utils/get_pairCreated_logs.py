#%%
from utils.bsc_client import w3, scan
from utils.pancake_utils import pancake_factory_address, pairCreated_topic, wbnb_topic
import datetime, os, time
import pandas as pd


# %%
def get_pairCreated_logs_by_timestamp(start, end):
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

        length = len(new_logs)
        if length > 0:
            start_block_no = int(new_logs[-1]['blockNumber'], 16)

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

    if os.path.exists(csv):
        logs = pd.read_csv(csv)

        update_logs = get_pairCreated_logs_by_timestamp(
            int(logs.iloc[-1]['timeStamp'], 16) + 1, end_timestamp_of_date)

        if len(update_logs) > 0:
            logs = pd.concat([logs, pd.DataFrame(update_logs)])
            logs.to_csv(csv, index=False)

        return logs
    else:
        logs = get_pairCreated_logs_by_timestamp(start_timestamp_of_date,
                                                 end_timestamp_of_date)

        logs = pd.DataFrame(logs)
        logs.to_csv(csv, index=False)

        return logs
