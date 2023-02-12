import json
import logging
import os

from web3 import Web3, HTTPProvider
from web3.datastructures import AttributeDict

from api.constant import Chain, DiamondContract


class SmartContract(object):

    default_providers = {
        Chain.ETHEREUM: "https://eth-rpc.gateway.pokt.network",
        Chain.OPTIMISM: "https://endpoints.omniatech.io/v1/op/mainnet/public",
        Chain.ARBITRUM_ONE: "https://endpoints.omniatech.io/v1/arbitrum/one/public",
        Chain.BNB_CHAIN: "https://bsc-dataseed3.binance.org",
        Chain.GNOSIS: "https://gnosis-mainnet.public.blastapi.io",
        Chain.POLYGON: "https://polygon-bor.publicnode.com",
    }
    
    @staticmethod
    def get_function_name(tx) -> str:
        return tx.functionName.split("(")[0]

    @staticmethod
    def get_default_provider(chain: Chain) -> Web3:
        return Web3(HTTPProvider(SmartContract.default_providers[chain]))

    def __init__(self, chain: Chain, address: str, abi_path: str) -> None:
        self.provider = SmartContract.get_default_provider(chain)

        self.address = address if self.provider.isChecksumAddress(address) else self.provider.toChecksumAddress(address)

        with open(abi_path, "r") as fp:
            self.abi = json.load(fp)

        self.contract = self.provider.eth.contract(self.address, abi=self.abi)

    @staticmethod
    def parse_bytes(item):
        if type(item) in [list, tuple]:
            item = [SmartContract.parse_bytes(_item) for _item in item]
        elif type(item) in [AttributeDict, dict]:
            item = {k: SmartContract.parse_bytes(v) for k, v in item.items()}
        elif isinstance(item, bytes):
            item = item.hex()
        return item

    def decode_input(self, input: str) -> dict:
        _, func_params = self.contract.decode_function_input(input)
        return {k: SmartContract.parse_bytes(v) for k, v in func_params.items()}


class ConnextDiamond(SmartContract):

    def __init__(self, chain: Chain, abi_path: str = "./abi/ConnextDiamond.json") -> None:
        address = DiamondContract.get_contract_address(chain)
        super().__init__(chain, address, abi_path)


class ERC20Token(SmartContract):

    def __init__(
        self, 
        chain: Chain, 
        address: str, 
        abi_path: str = "./abi/erc20.json",
        data_dir: str = "./data/token") -> None:
        super().__init__(chain, address, abi_path)
        self.cache_path = f"{data_dir}/{chain}/{self.address}.json"
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        self.load_data()

    def load_data(self):
        if os.path.exists(self.cache_path):
            logging.debug(f"Loading token data from {self.cache_path}")
            with open(self.cache_path, "r") as fp:
                data = json.load(fp)
                self.name = data["name"]
                self.symbol = data["symbol"]
                self.decimal = data["decimal"]
                self.total_supply = data["total_supply"]
        else:
            self.name = self.contract.functions.name().call()
            self.symbol = self.contract.functions.symbol().call()
            self.decimal = self.contract.functions.decimals().call()
            self.total_supply = self.contract.functions.totalSupply().call()
            self.save_data()
        
    def save_data(self):
        data = {
            "name": self.name,
            "symbol": self.symbol,
            "decimal": self.decimal,
            "total_supply": self.total_supply,
        }
        with open(self.cache_path, "w") as fp:
            json.dump(data, fp)
