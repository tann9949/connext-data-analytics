import logging
import os
import time
from typing import List, Union, Dict

from requests import Session

from api.constant import Chain



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
        }


class ScanAPI(object):

    _base_url = {
        Chain.ETHEREUM: 'https://api.etherscan.io/api',
        Chain.BNB_CHAIN: 'https://api.bscscan.com/api',
        Chain.POLYGON: 'https://api.polygonscan.com/api',
        Chain.OPTIMISM: 'https://api-optimistic.etherscan.io/api',
        Chain.ARBITRUM_ONE: 'https://api.arbiscan.io/api',
        Chain.GNOSIS: 'https://api.gnosisscan.io/api',
    }

    def __init__(self, chain: Chain) -> None:
        self.api_url = ScanAPI._base_url[chain]
        self.chain = chain
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

    def __get_apikey(self) -> str:
        """Get the next apikey in the list of apikeys. Using a round-robin"""
        apikey = self.apikeys[self.api_idx]
        self.api_idx = (self.api_idx + 1) % len(self.apikeys)
        return apikey

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

        # start request sessionts
        session = Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36"
        }

        # initial vars
        page = 1
        max_attempt = max_attempt
        wait_time = wait_time
        last_page = False

        while True:
            # iterate infinitely until reach the last page
            n_attempt = 0
            is_success = False

            while True:
                # iterate infinitely until get a successful response
                try:
                    if n_attempt > max_attempt:
                        # stop if reach the max attempt
                        raise Exception("Reach max attempt")
                        
                    # api params
                    _params = {
                        "module": "account",
                        "action": "txlist",
                        "address": address,
                        "startblock": startblock,
                        "endblock": endblock,
                        "page": page,
                        "offset": offset,
                        "sort": "asc",
                        "apikey": self.__get_apikey()
                    }
                    _params = {**_params, **kwargs}
                    
                    # make the request to the scan API
                    response = session.get(
                        url=self.api_url, 
                        params=_params, 
                        headers=headers,
                        timeout=timeout)

                    if response.status_code == 200:
                        # if success, parse the response
                        # and add the tx to the list
                        is_success = True
                        response = response.json()

                        if response["result"]:
                            # if there are txs, parse the response
                            for tx in response["result"]:
                                # add the from_address and to_address to the tx
                                # from was reserved keyword in python
                                tx["from_address"] = tx["from"]
                                tx["to_address"] = tx["to"]
                                # convert the tx to ScanTxn object
                                txs = ScanTxn(chain=self.chain, **tx)
                                transactions.append(txs)
                        else:
                            # if there are no txs, break the loop
                            # as we have reached the last page
                            last_page = True
                            break
                    else:
                        # if not success, raise an exception
                        # this will trigger the retry
                        raise ConnectionError("Response status code is not 200")

                    if is_success:
                        break

                except ConnectionError:
                    # if there is a connection error, retry
                    logging.warning(f"WARNING: Failed to fetch Etherscan API [{n_attempt}/{max_attempt}], retrying...")
                    time.sleep(wait_time)
                    n_attempt += 1

            if last_page:
                break
            page += 1

        return transactions
