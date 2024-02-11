.PHONY: help install prepare fmt clean build test build-release deploy contract_help
.DEFAULT_GOAL := help
SHELL:=/bin/bash

# Add help text after each target name starting with '\#\#'
help:   ## show this help
	@echo -e "Help for this makefile\n"
	@echo "Possible commands are:"
	@grep -h "##" $(MAKEFILE_LIST) | grep -v grep | sed -e 's/\(.*\):.*##\(.*\)/    \1: \2/'

install:  ## install Rust and Soroban-CLI
	# install Rust
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh && \
	# install Soroban and config
	rustup target add wasm32-unknown-unknown && \
	cargo install --locked soroban-cli --features opt && \

prepare:  ## Generate identity and fund
	soroban config network add --global testnet \
  		--rpc-url https://soroban-testnet.stellar.org:443 \
  		--network-passphrase "Test SDF Network ; September 2015" && \
	# generate addresses and add funds
	soroban config identity generate issuer && \
	soroban config identity generate distribution && \
	soroban config identity fund issuer --network testnet && \
	soroban config identity fund distribution --network testnet && \
	mkdir -p .soroban

fmt:
	cargo fmt --all

clean:
	cargo clean

build:
	soroban contract build
	@ls -l target/wasm32-unknown-unknown/release/*.wasm

test: build
	cargo test

build-release: build
	soroban contract optimize --wasm target/wasm32-unknown-unknown/release/seal_coin.wasm
	@ls -l target/wasm32-unknown-unknown/release/*.wasm

deploy: test build-release  ## Deploy Soroban contract to testnet
	soroban contract deploy \
  		--wasm target/wasm32-unknown-unknown/release/seal_coin.optimized.wasm \
  		--source-account issuer \
  		--network testnet \
  		> .soroban/seal_coin_id && \
  	cat .soroban/seal_coin_id

contract_help:
	soroban contract invoke \
    	--source-account distribution \
    	--network testnet \
    	--id $(shell cat .soroban/seal_coin_id) \
    	-- \
    	--help

contract_version:
	soroban contract invoke \
    	--source-account distribution \
    	--network testnet \
    	--id $(shell cat .soroban/seal_coin_id) \
    	-- \
    	version

contract_init:
	soroban contract invoke \
    	--source-account issuer \
    	--network testnet \
    	--id $(shell cat .soroban/seal_coin_id) \
    	-- \
    	init \
    	--admin $(shell soroban config identity address issuer) \
		--token $(shell soroban lab token id --asset SEAL:$(shell soroban config identity address issuer) --source-account issuer --network testnet) \

contract_test_update_sea_ice_extent_mint:
	soroban contract invoke \
    	--source-account issuer \
    	--network testnet \
    	--id $(shell cat .soroban/seal_coin_id) \
    	-- \
    	update_sea_ice_extent \
    	--issuer $(shell soroban config identity address issuer) \
    	--distributor $(shell soroban config identity address distribution) \
    	--doy 1 \
    	--sea_ice_extent 13923 \

contract_test_update_sea_ice_extent_burn:
	soroban contract invoke \
    	--source-account distribution \
    	--network testnet \
    	--id $(shell cat .soroban/seal_coin_id) \
    	-- \
    	update_sea_ice_extent \
    	--issuer $(shell soroban config identity address issuer) \
    	--distributor $(shell soroban config identity address distribution) \
    	--doy 1 \
    	--sea_ice_extent 13723 \

contract_reset:
	soroban contract invoke \
    	--source-account issuer \
    	--network testnet \
    	--id $(shell cat .soroban/seal_coin_id) \
    	-- \
    	reset

contract_upgrade: build-release
	soroban contract invoke \
    	--source-account issuer \
    	--network testnet \
    	--id $(shell cat .soroban/seal_coin_id) \
    	-- \
    	upgrade \
		--new_wasm_hash $(shell soroban contract install --source-account issuer --network testnet --wasm target/wasm32-unknown-unknown/release/seal_coin.optimized.wasm)
