import json
import logging
import os
import random
import time
from typing import Dict, List, Union

import requests

from api.constant import Chain
from api.contract import ConnextDiamond


class ScanTxn(object):

    def __init__(
        self,
        chain: Chain,
        blockNumber: Union[int, str],
        timeStamp: Union[int, str],
        hash: str,
        nonce: Union[int, str],
        blockHash: str,
        transactionIndex: Union[int, str],
        from_address: str,
        to_address: str,
        value: Union[int, str],
        gas: Union[int, str],
        gasPrice: Union[int, str],
        isError: Union[int, str],
        txreceipt_status: Union[int, str],
        input: str,
        contractAddress: str,
        cumulativeGasUsed: Union[int, str],
        gasUsed: Union[int, str],
        confirmations: Union[int, str],
        methodId: str,
        functionName: str,
        logs: List[dict] = None,
        **kwargs
    ) -> None:
        self.chain = chain
        if chain == Chain.ETHEREUM:
            self.scan_url = "https://etherscan.io/tx/"
        elif chain == Chain.BNB_CHAIN:
            self.scan_url = "https://bscscan.com/tx/"
        elif chain == Chain.OPTIMISM:
            self.scan_url = "https://optimistic.etherscan.io/tx/"
        elif chain == Chain.ARBITRUM_ONE:
            self.scan_url = "https://arbiscan.io/tx/"
        elif chain == Chain.GNOSIS:
            self.scan_url = "https://gnosisscan.io/tx/"
        elif chain == Chain.POLYGON:
            self.scan_url = "https://polygonscan.com/tx/"
        else:
            raise Exception("Chain {chain} not supported")

        self.blockNumber = int(blockNumber)
        self.timeStamp = int(timeStamp)
        self.hash = hash
        self.nonce = int(nonce)
        self.blockHash = blockHash
        self.transactionIndex = int(transactionIndex)
        self.from_address = from_address
        self.to_address = to_address
        self.value = int(value)
        self.gas = int(gas)
        self.gasPrice = int(gasPrice)
        self.isError = int(isError)
        self.txreceipt_status = int(txreceipt_status)
        self.input = input
        self.contractAddress = contractAddress
        self.cumulativeGasUsed = int(cumulativeGasUsed)
        self.gasUsed = int(gasUsed)
        self.confirmations = int(confirmations)
        self.methodId = methodId
        self.functionName = functionName

        self.logs = logs

        self.tx_url = f"{self.scan_url}/{self.hash}"

    def __repr__(self) -> str:
        return f"ScanTxn(url={self.tx_url}, hash={self.hash})"

    def to_json(self) -> Dict[str, Union[int, str]]:
        return {
            "chain": self.chain,
            "blockNumber": self.blockNumber,
            "timeStamp": self.timeStamp,
            "hash": self.hash,
            "nonce": self.nonce,
            "blockHash": self.blockHash,
            "transactionIndex": self.transactionIndex,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "value": self.value,
            "gas": self.gas,
            "gasPrice": self.gasPrice,
            "isError": self.isError,
            "txreceipt_status": self.txreceipt_status,
            "input": self.input,
            "contractAddress": self.contractAddress,
            "cumulativeGasUsed": self.cumulativeGasUsed,
            "gasUsed": self.gasUsed,
            "confirmations": self.confirmations,
            "methodId": self.methodId,
            "functionName": self.functionName,
            "tx_url": self.tx_url,
            "logs": self.logs,
        }

    @staticmethod
    def from_json(json_path: str) -> "ScanTxn":
        with open(json_path, "r") as f:
            json_obj = json.loads(f.read())
        return ScanTxn(**json_obj)


class ScanAPI(object):

    _base_url = {
        Chain.ETHEREUM: 'https://api.etherscan.io/api',
        Chain.BNB_CHAIN: 'https://api.bscscan.com/api',
        Chain.POLYGON: 'https://api.polygonscan.com/api',
        Chain.OPTIMISM: 'https://api-optimistic.etherscan.io/api',
        Chain.ARBITRUM_ONE: 'https://api.arbiscan.io/api',
        Chain.GNOSIS: 'https://api.gnosisscan.io/api',
    }

    def __init__(self, chain: Chain, apikey_schedule: str = "roundrobin") -> None:
        self.api_url = ScanAPI._base_url[chain]
        self.chain = chain
        self.diamond_contract = ConnextDiamond(self.chain)
        self.provider = ConnextDiamond.get_default_provider(self.chain)
        self.api_idx = 0
        
        if chain == Chain.ETHEREUM:
            self.apikeys = os.getenv("ETHERSCAN_APIKEYS").split(",")
        elif chain == Chain.BNB_CHAIN:
            self.apikeys = os.getenv("BSCSCAN_APIKEYS").split(",")
        elif chain == Chain.POLYGON:
            self.apikeys = os.getenv("POLYGONSCAN_APIKEYS").split(",")
        elif chain == Chain.OPTIMISM:
            self.apikeys = os.getenv("OPTIMISTICSCAN_APIKEYS").split(",")
        elif chain == Chain.ARBITRUM_ONE:
            self.apikeys = os.getenv("ARBITRUMSCAN_APIKEYS").split(",")
        elif chain == Chain.GNOSIS:
            self.apikeys = os.getenv("GNOSISSCAN_APIKEYS").split(",")
        else:
            raise Exception("Chain {chain} not supported")

        logging.debug(f"Using {len(self.apikeys)} apikeys for {chain}")

        self.apikey_schedule = apikey_schedule

    def get_apikey(self) -> str:
        """Get the next apikey in the list of apikeys. Using a round-robin"""
        if self.apikey_schedule == "roundrobin":
            logging.debug(f"Current apikey index: {self.api_idx}")
            self.api_idx = (self.api_idx + 1) % len(self.apikeys)
            logging.debug(f"New apikey index: {self.api_idx}")
            apikey = self.apikeys[self.api_idx]
            logging.debug(f"[{self.chain}] Using apikey ({self.api_idx}/{len(self.apikeys)})")
        elif self.apikey_schedule == "random":
            self.api_idx = random.choice(range(len(self.apikeys)))
            apikey = self.apikeys[self.api_idx]
            logging.debug(f"[{self.chain}] Using apikey ({self.api_idx}/{len(self.apikeys)})")
        return apikey

    def request_with_retry(
        self,
        url: str,
        params: Dict[str, str],
        max_attempt: int = 20,
        wait_time: float = 0.5,
        timeout: int = 10,
        **kwargs
    ) -> requests.Response:
        """Make a request to the etherscan api with retry"""
        # initial vars
        max_attempt = max_attempt
        wait_time = wait_time
        attempt = 0

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36"
        }

        while True:
            try:
                # make request
                params["apikey"] = self.get_apikey()
                response = requests.get(url, params=params, headers=headers, timeout=timeout, **kwargs)

                # check status code
                if response.status_code == 200:
                    if response.json().get("status") == "0" and response.json().get("message") != "No transactions found":
                        raise ConnectionError(response.json().get("message"))
                    return response.json()
                else:
                    raise ConnectionError(f"Request failed with status code {response.status_code}")
            except (ConnectionError, requests.exceptions.ReadTimeout) as e:
                # check if we have reached max attempt
                logging.warning(f"WARNING: Failed to fetch Etherscan API [{attempt}/{max_attempt}], retrying...")
                if attempt == max_attempt:
                    raise e

                # sleep for a bit
                time.sleep(wait_time)

                # increment attempt
                attempt += 1

    def get_transaction_receipt(
        self,
        tx_hash: str,
        timeout: int = 60,
        max_attempt: int = 20,
        wait_time: float = 0.5,
        **kwargs
    ) -> dict:
        """Get the transaction receipt for a specifed tx hash"""
        response = self.request_with_retry(
            url=self.api_url,
            params={
                "module": "proxy",
                "action": "eth_getTransactionReceipt",
                "txhash": tx_hash,
            },
            max_attempt=max_attempt,
            wait_time=wait_time,
            timeout=timeout,
            **kwargs
        )

        return response["result"]

    def get_transaction_by_address(
        self, 
        address: str, 
        startblock: int = 0,
        endblock: int = 999999999,
        offset: int = 1000,
        timeout: int = 60,
        max_attempt: int = 20,
        wait_time: float = 0.5,
        **kwargs) -> List[ScanTxn]:
        """Get the list of transactions for a specifed contracts"""
        # initialize empty txs
        transactions = []

        # initial vars
        page = 1
        last_page = False

        while True:
            # iterate infinitely until reach the last page

            logging.debug(f"Fetching page {page} for address {address}")
            response = self.request_with_retry(
                url=self.api_url,
                params={
                    "module": "account",
                    "action": "txlist",
                    "address": address,
                    "startblock": startblock,
                    "endblock": endblock,
                    "page": page,
                    "offset": offset,
                    "sort": "asc",
                },
                max_attempt=max_attempt,
                wait_time=wait_time,
                **kwargs)

            if response["result"]:
                # if there are txs, parse the response
                for tx in response["result"]:
                    if tx["isError"] == "1":
                        # skip failed txs
                        continue
                    # add the from_address and to_address to the tx
                    # from was reserved keyword in python
                    tx["from_address"] = tx["from"]
                    tx["to_address"] = tx["to"]
                    # convert the tx to ScanTxn object
                    try:
                        tx["input"] = self.diamond_contract.decode_input(tx["input"])
                    except ValueError as e:
                        # skip contract creation txs
                        logging.warning(f"WARNING: Failed to decode input [{self.chain} : {tx['hash']}]: {e}")
                        pass

                    txs = ScanTxn(chain=self.chain, **tx)
                    transactions.append(txs)
            else:
                # if there are no txs, break the loop
                # as we have reached the last page
                last_page = True
                break

            if last_page:
                break
            page += 1

        return transactions


    def resolve_blocktime(
        self, 
        blocktime: int,
        max_attempt: int = 5,
        wait_time: int = 1,
        timeout: int = 10,
        **kwargs) -> int:
        """Convert blocktime to unix timestamp"""
        response = self.request_with_retry(
            url=self.api_url,
            params={
                "module": "block",
                "action": "getblockreward",
                "blockno": blocktime,
            },
            max_attempt=max_attempt,
            wait_time=wait_time,
            timeout=timeout,
            **kwargs
        )

        return response["result"]["timeStamp"]
