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
    pub doy: u32,
}

#[contract]
pub struct SealCoinContract;

#[contractimpl]
impl SealCoinContract {
    pub fn version() -> u32 {
        2
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
        doy: u32,
        sea_ice_extent: u32,
    ) {
        if !is_initialized(&env) {
            panic!("contract has not been initialized");
        }

        // Store Seal Coin parameters
        env.storage().instance().set(
            &DataKey::SealData,
            &SealData {
                sea_ice_extent,
                doy,
            },
        );

        // Adjust supply level with given amount
        correct_supply(&env, &issuer, &distributor, &doy, &sea_ice_extent);
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

fn correct_supply(
    env: &Env,
    issuer: &Address,
    distributor: &Address,
    doy: &u32,
    sea_ice_extent: &u32,
) {
    if !is_initialized(env) {
        panic!("contract has not been initialized");
    }

    if !(1..367).contains(doy) {
        panic!("doy must be in [1, 366]");
    }

    if !(0..30_001).contains(sea_ice_extent) {
        // could have a better upper bound
        panic!("sea_ice_extent must be in [0, 30_000]");
    }

    let token_address: Address = env.storage().instance().get(&DataKey::Token).unwrap();

    // let ledger_timestamp = env.ledger().timestamp();
    let doy = *doy as usize;
    let sea_ice_extent = *sea_ice_extent as i32;

    let sea_ice_extent_history = historical_data::MEDIAN_EXTENT[doy - 1];
    let sea_ice_extent_history = sea_ice_extent_history as i32;
    let delta: i128 = (sea_ice_extent - sea_ice_extent_history).into();

    // convert delta extent to token amount e.g.
    // sea_ice_extent = 13976, MEDIAN_EXTENT = 14526
    // 13976-14526 = -550
    // -550 * 100 = -55k SEAL
    // * 1e7 to go to base unit
    let amount: i128 = delta * 100 * 10_000_000;
    let min_amount: i128 = 1000 * 10_000_000;

    if amount > min_amount {
        issuer.require_auth();
        let client = token::StellarAssetClient::new(env, &token_address);
        client.mint(distributor, &amount)
    } else if amount < -min_amount {
        distributor.require_auth();
        let client = token::Client::new(env, &token_address);
        client.burn(distributor, &amount.abs())
    }
}

mod test;
