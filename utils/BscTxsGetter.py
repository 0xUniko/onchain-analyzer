# %%
from typing import List
from utils.Scanner import Scanner
from utils.token.pancake_utils import router_input_decoder
import datetime, os, json, warnings
import pandas as pd


class BscTxsGetter:
    def __init__(self, proxies=None):
        self.proxies = proxies
        self.scanner = Scanner(proxies=proxies).__enter__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.scanner.__exit__(exc_type, exc_value, trace)
        return False

    def bep20_txs(self, address=None, contractaddress=None):
        startblock = 0
        txs = []
        flag = True
        rd = 0

        params = {}
        if address != None:
            params["address"] = address
        if contractaddress != None:
            params["contractaddress"] = contractaddress

        while flag:
            print("round:", rd)
            new_txs = self.scanner.scan(
                "account", "tokentx", startblock=startblock, **params
            )

            txs_hash = [x["hash"] for x in txs]
            txs.extend([tx for tx in new_txs if tx["hash"] not in txs_hash])

            if len(new_txs) != 10000:
                flag = False
            else:
                startblock = new_txs[-1]["blockNumber"]
                rd += 1

        return txs

    def all_txs(
        self,
        date: datetime.date,
        name="pcs_router_txs",
        address="0x10ed43c718714eb63d5aa57b78b54704e256024e",
    ):
        """
        get all transactions of a date
        """
        dirname = os.path.join("utils", "cache", name)

        if not os.path.exists(dirname):
            os.mkdir(dirname)

        cache_txs = os.path.join(dirname, f"{str(date)}.feather")

        if os.path.exists(cache_txs):
            txs: pd.DataFrame = pd.read_feather(cache_txs)

            last_tx = sorted(
                [f for f in os.listdir(dirname) if len(f) == 18 and f[-7:] == "feather"]
            )[-1][:10]

            if str(date) == last_tx:
                if not txs.empty:
                    _, endblock = Scanner.get_start_end_block_of_date(
                        date, proxies=self.proxies
                    )
                    startblock = txs.iloc[-1]["blockNumber"]
            else:
                txs.set_index("hash", inplace=True)
                return txs
        else:
            startblock, endblock = Scanner.get_start_end_block_of_date(
                date, proxies=self.proxies
            )
            txs = pd.DataFrame()

        print("startblock:", startblock, "endblock:", endblock)

        listdir = os.listdir(os.path.join(dirname, "tmp"))
        new_txs_collector = []
        flag = True

        while flag:
            print("startblock:", startblock)

            tmp = str(startblock) + ".json"
            if tmp in listdir:
                with open(os.path.join(dirname, "tmp", tmp), "r") as f:
                    new_txs = json.load(f)
            else:
                new_txs = self.scanner.scan(
                    "account",
                    "txlist",
                    address=address,
                    startblock=startblock,
                    endblock=endblock,
                )
                if not new_txs:
                    warnings.warn(f"startblock {startblock} is empty!")
                else:
                    with open(os.path.join(dirname, "tmp", tmp), "w") as f:
                        json.dump(new_txs, f)

            new_txs_collector = [
                tx for tx in new_txs_collector if tx["blockNumber"] != startblock
            ]

            if new_txs:
                new_txs_collector.extend([tx for tx in new_txs if tx["isError"] != "1"])

            if new_txs == None or len(new_txs) != 10000:
                flag = False
            else:
                startblock = new_txs[-1]["blockNumber"]

        txs = pd.concat([txs, pd.DataFrame(new_txs_collector)], ignore_index=True)
        if new_txs_collector:
            txs.to_feather(cache_txs)

        txs.set_index("hash", inplace=True)
        return txs

    def get_txs_and_external_accounts_holders(
        self,
        token_logs: pd.DataFrame,
        pair_logs: List[pd.DataFrame],
        holders: pd.Series,
        start_date: datetime.date,
        end_date: datetime.date = datetime.date.today(),
    ):
        hashs = []
        contract_holders = set(holders)

        hashs.extend(token_logs["transactionHash"])

        for log in pair_logs:
            hashs.extend(log["transactionHash"])

        hashs = set(hashs)
        txs = []

        while start_date <= end_date:
            print("start_date:", start_date)

            txs_date = self.all_txs(date=start_date)

            txs.append(txs_date.loc[list(set(txs_date.index).intersection(hashs))])

            contract_holders = contract_holders - set(txs_date["from"])

            start_date += datetime.timedelta(days=1)

        return set(holders) - contract_holders, pd.concat(txs)

    def get_router_liquidity_txs(self, date: datetime.date):
        txs = self.all_txs(date=date)

        txs = txs.join(
            txs.apply(
                lambda x: router_input_decoder.decode(x["input"]),
                axis=1,
                result_type="expand",
            )
        ).rename(columns={0: "method_name", 1: "data"})

        del txs["input"]

        return txs.loc[txs["method_name"].map(lambda x: "Liquidity" in x)]

    def get_txs_by_hashs(
        self,
        hashs: List[str],
        start_date: datetime.date,
        end_date: datetime.date.today(),
    ):
        hashs = set(hashs)
        txs = []

        while start_date <= end_date:
            print("start_date:", start_date)

            txs_date = self.all_txs(date=start_date)

            txs.append(txs_date.loc[[hash for hash in hashs if hash in txs_date.index]])

            start_date += datetime.timedelta(days=1)

        return pd.concat(txs)

    def get_txs_by_token_logs_and_pairs_logs(
        self,
        token_logs: pd.DataFrame,
        pair_logs: List[pd.DataFrame],
        start_date: datetime.date,
        end_date: datetime.date = datetime.date.today(),
    ):
        """
        Deprecated. Use get_txs_and_external_accounts_holders
        """
        hashs = []

        hashs.extend(token_logs["transactionHash"])

        for log in pair_logs:
            hashs.extend(log["transactionHash"])

        return self.get_txs_by_hashs(
            hashs=hashs, start_date=start_date, end_date=end_date
        )

    def get_router_txs_by_token(
        self,
        token: str,
        start_date: datetime.date,
        end_date: datetime.date = datetime.date.today(),
    ):
        """
        This function selects the token transactions by transaction input. It is slower than get_txs_and_external_accounts_holders.
        This function can be used i verification.
        """
        token = token.lower()
        txs = []

        def find_mvs_txs_in_router_txs(tx_input):
            if "swap" in tx_input[0]:
                return token in tx_input[1]["path"]

            if "Liquidity" in tx_input[0]:
                if "ETH" in tx_input[0]:
                    return tx_input[1]["token"] == token
                else:
                    return (
                        tx_input[1]["tokenA"] == token or tx_input[1]["tokenB"] == token
                    )

            return False

        while not start_date > end_date:
            print("start_date:", start_date)

            router_txs = self.all_txs(start_date)

            router_txs["input"] = router_txs["input"].map(router_input_decoder.decode)

            txs.append(
                router_txs.loc[router_txs["input"].map(find_mvs_txs_in_router_txs)]
            )

            start_date += datetime.timedelta(days=1)

        return pd.concat(txs)


# %%
