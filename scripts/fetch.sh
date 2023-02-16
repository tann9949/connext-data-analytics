#!/bin/bash

cd ..

# Fetch transactions from the network and store them in the database.
until python fetch_txn.py;
do
    echo "Restarting fetch_tx.py in 0.5 seconds";
    sleep 0.5;
done

# Fetch prices from the network and store them in the database.
until python fetch_price.py;
do
    echo "Restarting fetch_price.py in 0.5 seconds";
    sleep 0.5;
done
