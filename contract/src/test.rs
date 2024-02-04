#![cfg(test)]

use super::{SealCoinContract, SealCoinContractClient};
use soroban_sdk::testutils::{Address as _};
use soroban_sdk::{token, Address, Env};
use token::Client as TokenClient;
use token::StellarAssetClient as TokenAdminClient;


fn create_token_contract<'a>(e: &Env, admin: &Address) -> (TokenClient<'a>, TokenAdminClient<'a>) {
    let contract_address = e.register_stellar_asset_contract(admin.clone());
    (
        TokenClient::new(e, &contract_address),
        TokenAdminClient::new(e, &contract_address),
    )
}


#[test]
fn test() {
    // A default Soroban environment
    // is created and the contract (along with its client) is registered in it.
    let env = Env::default();
    env.mock_all_auths();

    let distributor = Address::generate(&env);
    let issuer = Address::generate(&env);
    let contract_admin = Address::generate(&env);

    let (token, issuer_client) = create_token_contract(&env, &issuer);
    issuer_client.mint(&distributor, &1_000_000_000);
    assert_eq!(token.balance(&distributor), 1_000_000_000);

    let contract_id = env.register_contract(None, SealCoinContract);
    let contract = SealCoinContractClient::new(&env, &contract_id);

    contract.init(&contract_admin, &token.address);

    // doy 0 -> 13.823
    // Mint
    contract.update_sea_ice_extent(&issuer, &distributor, &0, &23823);
    assert_eq!(token.balance(&distributor), 1_000_010_000);

    contract.update_sea_ice_extent(&issuer, &distributor, &0, &14823);
    assert_eq!(token.balance(&distributor), 1_000_010_000);

    // Burn
    contract.update_sea_ice_extent(&issuer, &distributor, &0, &3823);
    assert_eq!(token.balance(&distributor), 1_000_000_000);
}
