import json
import logging
from typing import List, Union, Optional

import pandas as pd
import requests

from api.constant import Chain


class BaseSubGraphQuery(object):

    def __init__(self, subgraph_url: str) -> None:
        self.url = subgraph_url

    def query(self, query: str):
        data = json.dumps({"query": query}).replace("\n", "").replace(" ", "")
        response = requests.post(
            self.url, 
            data=data)

        if response.status_code != 200:
            raise ConnectionError(response.text)

        return response.json()


class UniswapV3SubGraph(BaseSubGraphQuery):
    
    def __init__(self) -> None:
        super().__init__(subgraph_url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3")

    def get_weth_price(self, block: Optional[int] = None) -> float:
        """Get WETH price in USDC from ETH-USDC pool

        Returns:
            float: Price in USDC
        """
        pool_id = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
        result = self.get_pools(pool_id, block)

        # handle different return types from subgraph
        if isinstance(result, list):
            if len(result) != 1:
                logging.warning(f"Expected 1 result, got {len(result)}, returning first result")
            result = result[0]
        if "data" in result and "pools" in result["data"] and len(result["data"]["pools"]) == 1:
            result = result["data"]["pools"][0]

        weth_price = result["token0Price"]
        return weth_price

    def get_pools(self, pool_ids: Union[str, List[str]], block: Optional[int] = None) -> pd.DataFrame:
        if isinstance(pool_ids, str):
            pool_ids = [pool_ids]
        pool_ids = str(pool_ids)

        # construct query
        query = """{
            pools(
        """
        
        if block is not None:
            query += """block: {number: """ + str(block) + """},"""
        
        query += """
                where: {
                    id_in: """ + pool_ids.replace("'", '"') + """,
                }
            ) {
                id,
                token0 {
                    id
                    symbol
                    name
                },
                token1 {
                    id
                    symbol
                    name,
                },
                token0Price,
                token1Price,
                totalValueLockedUSD
            }
        }"""
        result = self.query(query)
        logging.debug(result)
        return result["data"]["pools"]
    

class EthereumBlocksSubGraph(BaseSubGraphQuery):

    def __init__(self) -> None:
        super().__init__(
            subgraph_url="https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks")

    def get_blocktime_from_unix(self, unix: int) -> int:
        unix = int(unix)

        query = """{
            blocks(
                first: 1
                orderBy: timestamp
                orderDirection: desc
                where: {timestamp_lt: """ + str(unix).replace("'", '"') + """}
            ) {
                id
                number
                timestamp
            }
        }"""
        result = self.query(query)
        result = [_r["number"] for _r in result["data"]["blocks"]]
        return result

    def get_unix_from_blocktime(self, blocktime: int) -> int:
        blocktime = str([blocktime]).replace("'", '"')
        
        query = """{
            blocks(
                first: 1
                orderBy: timestamp
                orderDirection: desc
                where: {number_in: """ + str(blocktime) + """}
            ) {
                id
                number
                timestamp
            }
        }"""
        result = self.query(query)
        result = [_r["timestamp"] for _r in result["data"]["blocks"]]
        return result


class ConnextSubgraph(BaseSubGraphQuery):

    def __init__(self, chain: Chain) -> None:
        self.chain = chain
        subgraph_url = ConnextSubgraph.get_subgraph_url(chain)
        super().__init__(
            subgraph_url=subgraph_url)
        
    @staticmethod
    def get_subgraph_url(chain: Chain) -> str:
        if chain == Chain.ETHEREUM:
            return "https://api.thegraph.com/subgraphs/name/connext/amarok-runtime-v0-mainnet"
        elif chain == Chain.POLYGON:
            return "https://api.thegraph.com/subgraphs/name/connext/amarok-runtime-v0-polygon"
        elif chain == Chain.GNOSIS:
            return "https://api.thegraph.com/subgraphs/name/connext/amarok-runtime-v0-gnosis"
        elif chain == Chain.ARBITRUM_ONE:
            return "https://api.thegraph.com/subgraphs/name/connext/amarok-runtime-v0-arbitrum-one"
        elif chain == Chain.OPTIMISM:
            return "https://api.thegraph.com/subgraphs/name/connext/amarok-runtime-v0-optimism"
        elif chain == Chain.BNB_CHAIN:
            return "https://api.thegraph.com/subgraphs/name/connext/amarok-runtime-v0-bnb"
        else:
            raise NotImplementedError(f"Chain {chain} not supported")
        
    def get_ori_transfer(self, tx_hash: str) -> dict:
        query = """{
            originTransfers(
                where: {
                transactionHash: \"""" + str(tx_hash) + """\"
                }
            ) {
                timestamp

                chainId
                transferId
                nonce
                to
                delegate
                receiveLocal
                callData
                slippage
                relayerFee
                originSender
                originDomain
                destinationDomain
                transactionHash
                bridgedAmt
                status
                timestamp
                normalizedIn
                asset {
                    id
                    adoptedAsset
                    canonicalId
                    canonicalDomain
                }
            }
        }"""
        result = self.query(query)
        return result
    
    def get_dest_transfer(self, transfer_id: str) -> dict:
        query = """{
            destinationTransfers(
                where: {
                transferId: \"""" + str(transfer_id) + """\"
                }
            ) {
                chainId
                nonce
                transferId
                to
                callData
                originDomain
                destinationDomain
                delegate
                
                asset {
                    id
                }
                bridgedAmt
                
                status
                routers {
                    id
                }
                originSender
                
                executedCaller
                executedTransactionHash
                executedTimestamp
                executedGasPrice
                executedGasLimit
                executedBlockNumber
                
                reconciledCaller
                reconciledTransactionHash
                reconciledTimestamp
                reconciledGasPrice
                reconciledGasLimit
                reconciledBlockNumber
                routersFee
                slippage
            }
        }"""
        result = self.query(query)
        return result
