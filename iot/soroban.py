"""Helper function to call the Soroban Contract

Based on
https://github.com/StellarCN/py-stellar-base/blob/main/examples/soroban_payment.py
"""
import time

from stellar_sdk import Keypair, Network, SorobanServer, TransactionBuilder, scval
from stellar_sdk import xdr as stellar_xdr
from stellar_sdk.exceptions import PrepareTransactionException
from stellar_sdk.soroban_rpc import GetTransactionStatus, SendTransactionStatus
from stellar_sdk.xdr import SCVal

rpc_server_url = "https://soroban-testnet.stellar.org:443"
soroban_server = SorobanServer(rpc_server_url)
network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE


def soroban_invoke(secret_key: str, contract_id: str, function_name: str, args: list[SCVal]):
    address_kp = Keypair.from_secret(secret_key)
    address_source = soroban_server.load_account(address_kp.public_key)

    tx = (
        TransactionBuilder(address_source, network_passphrase, base_fee=500)
        .add_time_bounds(0, 0)
        .append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name=function_name,
            parameters=args,
        )
        .build()
    )

    response = False

    try:
        tx = soroban_server.prepare_transaction(tx)
    except PrepareTransactionException as e:
        print(f"Got exception: {e.simulate_transaction_response}")
        return response

    tx.sign(address_kp)
    print(f"Signed XDR:\n{tx.to_xdr()}")

    send_transaction_data = soroban_server.send_transaction(tx)
    print(f"sent transaction: {send_transaction_data}")
    if send_transaction_data.status != SendTransactionStatus.PENDING:
        print("send transaction failed")
        return response
    while True:
        print("waiting for transaction to be confirmed...")
        get_transaction_data = soroban_server.get_transaction(send_transaction_data.hash)
        if get_transaction_data.status != GetTransactionStatus.NOT_FOUND:
            break
        time.sleep(3)

    print(f"transaction: {get_transaction_data}")

    response = False
    if get_transaction_data.status == GetTransactionStatus.SUCCESS:
        transaction_meta = stellar_xdr.TransactionMeta.from_xdr(
            get_transaction_data.result_meta_xdr
        )
        if transaction_meta.v3.soroban_meta.return_value.type == stellar_xdr.SCValType.SCV_VOID:  # type: ignore[union-attr]
            print("send response")
            response = True
    else:
        print(f"Transaction failed: {get_transaction_data.result_xdr}")

    return response
