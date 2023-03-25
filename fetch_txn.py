import logging

from dotenv import load_dotenv

from api.connext import ConnextAPI, ConnextLPTransferAPI
logging.basicConfig(level=logging.DEBUG)


def main():
    load_dotenv(".env")
    _ = ConnextAPI(data_dir="data").load_txs()
    _ = ConnextLPTransferAPI(data_dir="data").load_transfers()


if __name__ == "__main__":
    main()
