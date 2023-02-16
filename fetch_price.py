import logging

from api.price import WETHPriceFetcher
logging.basicConfig(level=logging.DEBUG)


def main():
    fetcher = WETHPriceFetcher()
    fetcher.multiprocess_fetch(num_workers=30)


if __name__ == "__main__":
    main()
