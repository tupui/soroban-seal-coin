# Seal Coin

<table align="center" border="0">
<tr>
<td><img src="doc/soroban-wordmark-temp.svg" alt="Soroban" width="250"/></td>
<td><img src="doc/COLOUR-Raspberry-Pi-Symbol-Registered.png" alt="Soroban" width="90"/></td>
</tr>
</table>

The goal of this project is to explore with IOT and
[Soroban](https://soroban.stellar.org) - Stellar Smart Contract.

[Stellar](https://stellar.org) is one of the most used blockchain technology.
It offers concrete real world applications such as ease of cross border
payments, tokenization of real world assets. Since January 2024, things are
getting even better with the ability to write Smart Contracts. In the Stellar
ecosystem, these are called *Soroban contracts*. 

## Rational

### Seal




### Sea Ice Index

https://nsidc.org/data/seaice_index
https://nsidc.org/sites/default/files/g02135-v003-userguide_1_1.pdf

### Seal Coin



## Project structure

There are 2 folders:

- *iot*: relates to the client side, Raspberry Pi code.
- *contract*: the Soroban contract itself.

In each folder, there is a handy Makefile with useful commands. Let's go
through the IOT part first, and then we will cover the contract.

## Raspberry Pi

...

### Hardware

I am using a Raspberry Pi Zero 2 W. BOM:

- Raspberry Pi Zero 2 W
- Ultrasonic sensor HC-SR04
- Peristaltic pump 12V DC
- Adafruit TB6612 1.2A DC/Stepper Motor Driver Breakout Board
- 12V DC power supply
- E-Paper HAT 2.13" 250x122

See `iot/seal_coin_supply.py` for details on which GPIO to connect, it's very
straightforward:

- ...

![Raspberry Pi diagram](doc/diagram.png)

### Python service

After a classical headless setup of the Raspberry Pi, install everything Python:
```bash
ssh grogu@pumpit -i .ssh/raspberrypi_zero
sudo apt-get install libopenblas-dev
cd iot
python -m venv venv
source venv/bin/activate
pip install .
# And some variables needed to run the Soroban contract:
# Hash of the contract and address of the player/claimant
export CONTRACT_HASH_PUMPIT=...
export CLAIMANT_ADDR_SECRET_PUMPIT=...
```

To run the client (provided the contract is initialized, see bellow):

```bash
python seal_coin_supply.py
```

Behind the scene, ...

## Soroban - Stellar Smart Contract

We define a Smart Contract that hold a claimable balance. When conditions are
met, the balance is transferred to a claimant.

*Note: all commands are listed in a convenient Makefile in the contract folder.*

### Setup
These steps are to be done on any machine, not the Pi(s).

Following the Soroban [doc](https://soroban.stellar.org/docs), we setup a
Soroban local environment and install all dependencies. 
```bash
cd contract
# install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# install Soroban and config
rustup target add wasm32-unknown-unknown
cargo install --locked soroban-cli --features opt
```

In the following, we will be using *testnet*. Another option for playing
around is to use a docker image to run an actual Stellar network locally.
It's very simple to do as they provide a ready-to-use
[image](https://hub.docker.com/r/stellar/quickstart).

```bash
soroban config network add --global testnet
	--rpc-url https://soroban-testnet.stellar.org:443
	--network-passphrase "Test SDF Network ; September 2015"
```

We create (at least) two accounts on testnet and add some funds (in XLM).
Here I have `mando` and `grogu`. `mando` will be used as the admin of the
contract, and it will also be the one giving up some of its funds to deposit
on the contract.

```bash
# generate addresses
soroban config identity generate grogu
soroban config identity generate mando
# and add funds
soroban config identity fund grogu --network testnet
soroban config identity fund mando --network testnet
mkdir -p .soroban
```
