import logging
import multiprocessing as mp
import os
from typing import Dict, List, Optional

import pandas as pd

from api.connext import ConnextAPI
from api.subgraph import EthereumBlocksSubGraph, UniswapV3SubGraph
from api.contract import SmartContract
from api.constant import Chain


class WETHPriceFetcher(object):
    """Class to fetch historical prices from
    UniSwapV3 Subgraph, and store them in a cache
    """

    def __init__(
        self,
        data_dir: str = "data",) -> None:
        """
        :param data_dir: directory to store cache
        """
        self.data_dir = data_dir
        self.save_path = f"{self.data_dir}/amarok_prices/weth.csv"
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        if not os.path.exists(self.save_path):
            with open(self.save_path, "w") as fp:
                fp.write("blocktime,unixtime,price\n")

        self.eth_block_sg = EthereumBlocksSubGraph()
        self.univ3_sg = UniswapV3SubGraph()

    def load_cache(self) -> pd.DataFrame:
        """Load cache from data directory"""
        logging.info("Loading cache")
        return pd.read_csv(self.save_path)

    def fetch_eth_price(self, blocktime: int) -> None:
        """Fetch price of token at blocktime and save to cache
        """
        unixtime = self.eth_block_sg.get_unix_from_blocktime(blocktime)
        if isinstance(unixtime, list):
            if len(unixtime) == 1:
                unixtime = unixtime[0]
            if len(unixtime) > 1:
                logging.warning(f"Got multiple unixtimes for blocktime {blocktime}, using first")
            else:
                logging.warning(f"Got no unixtimes for blocktime {blocktime}, skipping")
                return
        
        prices = self.univ3_sg.get_weth_price(blocktime)

        
        with open(self.save_path, "a") as fp:
            fp.write(f"{blocktime},{unixtime},{prices}\n")

    def sort_cache(self) -> None:
        """Sort cache by blocktime"""
        df = self.load_cache()
        df = df.sort_values("blocktime").drop_duplicates()
        df.to_csv(self.save_path, index=False)
    
    def multiprocess_fetch(self, num_workers: Optional[int] = None) -> Dict[str, Dict[str, float]]:
        """Fetch prices of tokens at blocktimes

        :param blocktimes: blocktimes to fetch prices at

        :returns: dict of prices in the following format:
            {
                "token": {
                    "blocktime": blocktime,
                    "unixtime": unixtime,
                    "price": price,
                }
            }
        """
        if num_workers is None:
            num_workers = mp.cpu_count() - 1
        # get blocktimes
        provider = SmartContract.get_default_provider(Chain.ETHEREUM)
        start_block = ConnextAPI.get_init_block(Chain.ETHEREUM)
        end_block = provider.eth.get_block_number()

        data = self.load_cache()
        blocks = sorted(set(range(start_block, end_block)) - set(data["blocktime"].unique()))
        logging.info(f"Fetching prices from block {start_block} to {end_block} ({len(blocks)} blocks)")
        
        pool = mp.Pool(num_workers)
        pool.map(
            self.fetch_eth_price, 
            blocks)
        self.sort_cache()
