class Chain:
    ETHEREUM = "ethereum"
    OPTIMISM = "optimism"
    ARBITRUM_ONE = "arbitrum_one"
    BNB_CHAIN = "bnb_chain"
    GNOSIS = "gnosis"
    POLYGON = "polygon"


class DiamondContract:
    ETHEREUM = "0x8898B472C54c31894e3B9bb83cEA802a5d0e63C6"
    OPTIMISM = "0x8f7492de823025b4cfaab1d34c58963f2af5deda"
    ARBITRUM_ONE = "0xEE9deC2712cCE65174B561151701Bf54b99C24C8"
    BNB_CHAIN = "0xCd401c10afa37d641d2F594852DA94C700e4F2CE"
    GNOSIS = "0x5bb83e95f63217cda6ae3d181ba580ef377d2109"
    POLYGON = "0x11984dc4465481512eb5b777E44061C158CF2259"

    @staticmethod
    def get_contract_address(chain: Chain) -> str:
        if chain == Chain.ETHEREUM:
            return DiamondContract.ETHEREUM
        elif chain == Chain.OPTIMISM:
            return DiamondContract.OPTIMISM
        elif chain == Chain.ARBITRUM_ONE:
            return DiamondContract.ARBITRUM_ONE
        elif chain == Chain.BNB_CHAIN:
            return DiamondContract.BNB_CHAIN
        elif chain == Chain.GNOSIS:
            return DiamondContract.GNOSIS
        elif chain == Chain.POLYGON:
            return DiamondContract.POLYGON
        else:
            raise Exception("Chain {chain} not supported")
