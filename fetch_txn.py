import logging

from dotenv import load_dotenv

from api.connext import ConnextAPI
logging.basicConfig(level=logging.DEBUG)


def main():
    load_dotenv(".env")
    api = ConnextAPI(data_dir="data")
    _ = api.load_txs()


if __name__ == "__main__":
    main()
