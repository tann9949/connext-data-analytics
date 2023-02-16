import json
import logging
import multiprocessing as mp
import os
from glob import glob
from typing import Dict, List

from api.constant import Chain, DiamondContract
from api.scan import ScanAPI, ScanTxn


class ConnextAPI(object):
    """
    Connext API
    """

    def __init__(
        self, 
        data_dir: str = "data",) -> None:
        """
        :param data_dir: directory to store cache
        :param config_path: path to config file
        """
        self.data_dir = data_dir
        self.scan_api = {
            Chain.ETHEREUM: ScanAPI(Chain.ETHEREUM),
            Chain.BNB_CHAIN: ScanAPI(Chain.BNB_CHAIN),
            Chain.POLYGON: ScanAPI(Chain.POLYGON),
            Chain.OPTIMISM: ScanAPI(Chain.OPTIMISM),
            Chain.GNOSIS: ScanAPI(Chain.GNOSIS),
            Chain.ARBITRUM_ONE: ScanAPI(Chain.ARBITRUM_ONE),
        }

    @staticmethod
    def get_init_block(chain: Chain = Chain.ETHEREUM) -> int:
        """Get initial block for chain"""
        if chain == Chain.ETHEREUM:
            return 16233067
        elif chain == Chain.BNB_CHAIN:
            return 24097171
        elif chain == Chain.POLYGON:
            return 37100615
        elif chain == Chain.OPTIMISM:
            return 53024542
        elif chain == Chain.GNOSIS:
            return 25562300
        elif chain == Chain.ARBITRUM_ONE:
            return 47824792
        else:
            raise ValueError(f"Invalid chain {chain}")

    def load_cache(self) -> Dict[Chain, List[ScanTxn]]:
        """Load cache from data directory"""
        logging.info("Loading cache")
        data_path = f"{self.data_dir}/amarok_txs"
        if not os.path.exists(data_path):
            # create empty cache
            logging.info("Cache not found, creating empty cache")
            return {chain: [] for chain in self.scan_api.keys()}
        else:
            # load cache
            logging.info("Cache found, loading cache")
            data = {chain: [] for chain in self.scan_api.keys()}
            for chain in self.scan_api.keys():
                for tx in os.listdir(f"{data_path}/{chain}"):
                    with open(f"{data_path}/{chain}/{tx}", "r") as fp:
                        # logging.debug(f"Loading {tx} from `{data_path}/{chain}/{tx}`")
                        data[chain].append(ScanTxn(**json.load(fp)))
            # sort by block number
            data = {chain: sorted(data[chain], key=lambda x: x.blockNumber) for chain in data.keys()}
            return data

    def save_cache(self, data: Dict[Chain, List[ScanTxn]]) -> None:
        """Save cache to data directory"""
        data = data.copy()
        logging.info("Saving cache")
        data_path = f"{self.data_dir}/amarok_txs"
        # convert to dict
        for chain in data.keys():
            for tx in data[chain]:
                save_path = f"{data_path}/{chain}/{tx.hash}.json"
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "w") as fp:
                    json.dump(tx.to_json(), fp, indent=4)

    @staticmethod
    def resolve_receipt(tx_path: str) -> bool:
        """Resolve transaction receipt"""
        tx = ScanTxn.from_json(tx_path)

        if tx.logs is not None:
            logging.debug(f"Transaction {tx.hash} already resolved, skipping")
            return False

        logging.debug(f"Resolving transaction {tx.hash}")
        receipt = ScanAPI(tx.chain, apikey_schedule="random").get_transaction_receipt(
            tx.hash, timeout=10, max_attempt=10, wait_time=1)
        if isinstance(receipt, str):
            raise TypeError(f"Error resolving transaction {tx.hash}: {receipt}")
        logs = receipt["logs"]
        tx.logs = logs

        with open(tx_path, "w") as fp:
            json.dump(tx.to_json(), fp, indent=4)

        return True

    def load_txs(self) -> Dict[Chain, List[ScanTxn]]:
        """Load transactions from scan API"""
        data = self.load_cache()
        # get latest block number
        latest_block = {
            chain: max([tx.blockNumber for tx in data[chain]]) + 1 if data[chain] else 0
            for chain in self.scan_api.keys()
        }

        # verbose logging
        for chain in self.scan_api.keys():
            logging.info(f"Latest block number on {chain}: {latest_block[chain]}")

        # load transactions from scan API
        logging.info("Loading transactions from scan API")
        amarok_txs = {
            chain: self.scan_api[chain].get_transaction_by_address(
                DiamondContract.get_contract_address(chain), 
                startblock=latest_block[chain])
            for chain in [
                Chain.ETHEREUM, Chain.POLYGON, Chain.ARBITRUM_ONE, Chain.GNOSIS, Chain.BNB_CHAIN, Chain.OPTIMISM]}

        # if no new transactions, return cache
        for chain in self.scan_api.keys():
            logging.info(f"Number of new transactions on {chain}: {len(amarok_txs[chain])}")

        if all([len(amarok_txs[chain]) == 0 for chain in self.scan_api.keys()]):
            logging.info("No new transactions, returning cache")
        else:
            # update cache
            logging.info("Updating cache")
            for chain in self.scan_api.keys():
                data[chain] += amarok_txs[chain]

            # sort by block number
            for chain in self.scan_api.keys():
                data[chain] = sorted(data[chain], key=lambda x: x.blockNumber)

            # save cache
            self.save_cache(data)

        # multiprocessing resolve receipt
        logging.info("Resolving receipt")
        # create cache files
        cache_files = []
        for json_path in sorted(glob(f"{self.data_dir}/amarok_txs/**/*.json")):
            tx = ScanTxn.from_json(json_path)
            if tx.logs is None:
                cache_files.append(json_path)
        # start multiprocessing
        with mp.Pool(12) as pool:
            pool.map(ConnextAPI.resolve_receipt, cache_files)

        return data
    