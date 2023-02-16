# Connext Liquidity Bootstraping Analytics
This repository was used to provide an analysis on Connext's liquidity Bootstraping campaign.

## Requirements
The development use the following setups:
- Python 3.10
- MAC OSX (Linux-based OS should also works just fine)

#### 1. (Optinal) Create `virtualenv`
Use your preferred python version (recommend `3.10`+) to create a virtual environment
```bash
# create virtualenv
python -m venv .env
# activate virtualenv
source .env/bin/activate
```
This will create a python environment specifically for this workspace so that you wouldn't need to concern about any packaging conflict with your legacy python (if you have one)

#### 2. Install dependencies
Install dependencies by calling the following command:
```bash
pip install -r requirements.txt
```

## Usage

### Preparing environment variables
This repository assumes you have API keys from block explorer. You can add multiple keys seperated by commas (e.g. `ETHERSCAN_APIKEYS="key1,key2,key3") to distribute API call loads.

An example of `.env` file configuration can be found at [`.env.example`](./.env.example)


### Fething historical transactions
We provide an analytics using the following procedure:
1. Fetching historical transaction data via Block Explorer API
2. Aggregates and transform into a readible `csv`
3. Provide an analysis on a jupyter notebook
Thus, it's important to fetch the historical data first. To fetch the historical data, run the following command:
```bash
cd scripts
./fetch.sh
```
This could take a while as it fetch all transaction data as well as transaction receipt

### Using notebooks
Activate the python environment according to this [section](#1-optinal-create-virtualenv), if you have one. Then, run the following command:
```bash
jupyter-lab
```
This command will instantiate the jupyter notebook server. Navitage to [`notebooks`](./notebooks/) directory, and open [`playground.ipynb`](./notebooks/playground.ipynb).

## Contribution
The guideline for contributing procedure is as follows:
1. Open an issue, specifying the contribution
2. Fork this repository, and work using different branches
3. Open Pull Request


## Author
`chompk.eth#9502`
