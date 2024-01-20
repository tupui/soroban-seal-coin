//! # Seal Coin Supply Control Soroban Contract
//!
//! The contract allows to control the supply of Seal Coin on the distribution
//! account.
//!
//! If the Sea Ice Extent drops, tokens are burned. And vice-versa.
//!
//! This contract is to be used by the accompanying IOT code which runs on
//! a Raspberry Pi.

#![no_std]

mod historical_data;
use soroban_sdk::{contract, contractimpl, contracttype, token, Address, BytesN, Env};


#[derive(Clone)]
#[contracttype]
pub enum DataKey {
    Admin,    // Contract administrator
    Token,    // Seal Coin address
    SealData, // Hold the Seal information
}

#[derive(Clone)]
#[contracttype]
pub struct SealData {
    pub sea_ice_extent: u32,
}

#[contract]
pub struct SealCoinContract;

#[contractimpl]
impl SealCoinContract {
    pub fn version() -> u32 {
        1
    }

    pub fn init(env: Env, admin: Address, token: Address) {
        env.storage().instance().set(&DataKey::Admin, &admin);
        env.storage().instance().set(&DataKey::Token, &token);
    }

    /// Update the sea_ice_extent value on-chain
    pub fn update_sea_ice_extent(
        env: Env,
        issuer: Address,
        distributor: Address,
        sea_ice_extent: u32,
    ) {
        if !is_initialized(&env) {
            panic!("contract has not been initialized");
        }

        // Store Seal Coin parameters
        env.storage()
            .instance()
            .set(&DataKey::SealData, &SealData { sea_ice_extent });

        // Adjust supply level with given amount
        correct_supply(env, issuer, distributor, sea_ice_extent);
    }

    /// Reset the contract by deleting the token and coin data.
    pub fn reset(env: Env) {
        let admin: Address = env.storage().instance().get(&DataKey::Admin).unwrap();
        admin.require_auth();

        env.storage().instance().remove(&DataKey::Token);
        env.storage().instance().remove(&DataKey::SealData);
    }

    pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>) {
        let admin: Address = env.storage().instance().get(&DataKey::Admin).unwrap();
        admin.require_auth();

        env.deployer().update_current_contract_wasm(new_wasm_hash);
    }
}

// Helper functions

fn is_initialized(env: &Env) -> bool {
    env.storage().instance().has(&DataKey::Admin) && env.storage().instance().has(&DataKey::Token)
}

fn correct_supply(env: Env, issuer: Address, distributor: Address, sea_ice_extent: u32) {
    if !is_initialized(&env) {
        panic!("contract has not been initialized");
    }
    issuer.require_auth();
    distributor.require_auth();

    let token = env.storage().instance().get(&DataKey::Token).unwrap();
    let client = token::Client::new(&env, &token);

    // let ledger_timestamp = env.ledger().timestamp();
    // let doy = ...;
    let doy = 1;
    let amount: i128 = (sea_ice_extent - historical_data::MEDIAN_EXTENT[doy]).into();

    if amount > 0 {
        client.transfer(&issuer, &distributor, &amount)
    } else if amount < 0 {
        client.burn(&distributor, &amount.abs())
    } else {
    }
}