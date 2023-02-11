import json
import logging
import os
from typing import Dict, List

from omegaconf import OmegaConf

from api.constant import Chain
from api.scan import ScanAPI, ScanTxn


class ConnextAPI(object):
    """
    Connext API
    """

    def __init__(
        self, 
        data_dir: str = "data",
        config_path: str = "conf/networks.yaml") -> None:
        """
        :param data_dir: directory to store cache
        :param config_path: path to config file
        """
        self.data_dir = data_dir
        self.cfg = OmegaConf.load(config_path)
        self.scan_api = {
            Chain.ETHEREUM: ScanAPI(Chain.ETHEREUM),
            Chain.BNB_CHAIN: ScanAPI(Chain.BNB_CHAIN),
            Chain.POLYGON: ScanAPI(Chain.POLYGON),
            Chain.OPTIMISM: ScanAPI(Chain.OPTIMISM),
            Chain.GNOSIS: ScanAPI(Chain.GNOSIS),
            Chain.ARBITRUM_ONE: ScanAPI(Chain.ARBITRUM_ONE),
        }

    def load_cache(self) -> Dict[Chain, List[ScanTxn]]:
        """Load cache from data directory"""
        logging.info("Loading cache")
        data_path = f"{self.data_dir}/amarok_txs.json"
        if not os.path.exists(data_path):
            # create empty cache
            logging.info("Cache not found, creating empty cache")
            return {chain: [] for chain in self.scan_api.keys()}
        else:
            # load cache
            logging.info("Cache found, loading cache")
            with open(data_path, "r") as fp:
                data = json.load(fp)
            # convert to ScanTxn
            for chain in data.keys():
                data[chain] = [ScanTxn(**tx) for tx in data[chain]]
            return data

    def save_cache(self, data: Dict[Chain, List[ScanTxn]]) -> None:
        """Save cache to data directory"""
        data = data.copy()
        logging.info("Saving cache")
        data_path = f"{self.data_dir}/amarok_txs.json"
        # convert to dict
        for chain in data.keys():
            data[chain] = [tx.to_json() for tx in data[chain]]
        with open(data_path, "w") as fp:
            json.dump(data, fp, indent=4)

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
            chain: ScanAPI(chain).get_transaction_by_address(self.cfg.get(chain).address, startblock=latest_block[chain])
            for chain in [
                Chain.ETHEREUM, Chain.POLYGON, Chain.OPTIMISM, Chain.ARBITRUM_ONE, Chain.GNOSIS, Chain.BNB_CHAIN]}

        # if no new transactions, return cache
        for chain in self.scan_api.keys():
            logging.info(f"Number of new transactions on {chain}: {len(amarok_txs[chain])}")

        if all([len(amarok_txs[chain]) == 0 for chain in self.scan_api.keys()]):
            logging.info("No new transactions, returning cache")
            return data
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

        return data
    