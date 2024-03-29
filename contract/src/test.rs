#![cfg(test)]

use super::{SealCoinContract, SealCoinContractClient};
use soroban_sdk::testutils::Address as _;
use soroban_sdk::{token, Address, Env};
use token::Client as TokenClient;
use token::StellarAssetClient as TokenAdminClient;

#[test]
fn test() {
    // A default Soroban environment
    // is created and the contract (along with its client) is registered in it.
    let env = Env::default();
    env.mock_all_auths();

    // Create Token
    let issuer = Address::generate(&env);
    let distributor = Address::generate(&env);

    let token_address = env.register_stellar_asset_contract(issuer.clone());
    let token = TokenClient::new(&env, &token_address);
    let issuer_client = TokenAdminClient::new(&env, &token_address);

    // 1e7 diff between minimal unit and unit itself
    let genesis_amount: i128 = 1_000_000_000 * 10_000_000;

    assert_eq!(token.balance(&distributor), 0);
    issuer_client.mint(&distributor, &genesis_amount);
    assert_eq!(token.balance(&distributor), genesis_amount);

    let contract_admin = Address::generate(&env);
    let contract_id = env.register_contract(None, SealCoinContract);
    let contract = SealCoinContractClient::new(&env, &contract_id);
    contract.init(&contract_admin, &token_address);

    // doy 1 -> 13.823
    // 10K diff -> 1M token diff
    // Mint
    let delta = 13823 + 100; // result in +10K
    contract.update_sea_ice_extent(&issuer, &distributor, &1, &delta);
    let new_amount: i128 = genesis_amount + 10_000 * 10_000_000;
    assert_eq!(token.balance(&distributor), new_amount);

    // increment too small <1000
    let delta = 13823 + 10; // result in +1K
    contract.update_sea_ice_extent(&issuer, &distributor, &1, &delta);
    assert_eq!(token.balance(&distributor), new_amount);

    // Burn
    let delta = 13823 - 100; // result in -10K
    contract.update_sea_ice_extent(&issuer, &distributor, &1, &delta);
    assert_eq!(token.balance(&distributor), genesis_amount);
}
