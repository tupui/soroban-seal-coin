"""Helper function to call the Soroban Contract

Based on
https://github.com/StellarCN/py-stellar-base/blob/main/examples/soroban_payment.py
"""
import time

from stellar_sdk import Keypair, Network, SorobanServer, TransactionBuilder
from stellar_sdk import xdr as stellar_xdr
from stellar_sdk.exceptions import SdkError
from stellar_sdk.soroban_rpc import GetTransactionStatus, SendTransactionStatus
from stellar_sdk.xdr import SCVal

rpc_server_url = "https://soroban-testnet.stellar.org:443"
soroban_server = SorobanServer(rpc_server_url)
network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE


def soroban_invoke(
    secret_key: str, contract_id: str, function_name: str, args: list[SCVal],
    *,
    preflight: bool = True,
    timeout_count: int = 10
):
    address_kp = Keypair.from_secret(secret_key)
    address_source = soroban_server.load_account(address_kp.public_key)

    tx = (
        TransactionBuilder(address_source, network_passphrase, base_fee=200_000)
        .add_time_bounds(0, 0)
        .append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name=function_name,
            parameters=args,
        )
        .build()
    )

    if preflight:
        tx = soroban_server.prepare_transaction(tx)

    tx.sign(address_kp)
    send_transaction_data = soroban_server.send_transaction(tx)

    if send_transaction_data.status != SendTransactionStatus.PENDING:
        raise SdkError("Failed to send transaction")

    i = 0
    while i < timeout_count:
        get_transaction_data = soroban_server.get_transaction(send_transaction_data.hash)
        if get_transaction_data.status != GetTransactionStatus.NOT_FOUND:
            break
        time.sleep(3)
        i += 1
    else:
        raise SdkError("Timeout: could not validate transaction")

    if get_transaction_data.status == GetTransactionStatus.SUCCESS:
        transaction_meta = stellar_xdr.TransactionMeta.from_xdr(
            get_transaction_data.result_meta_xdr
        )
        if transaction_meta.v3.soroban_meta.return_value.type == stellar_xdr.SCValType.SCV_VOID:  # type: ignore[union-attr]
            return transaction_meta
    else:
        raise SdkError(f"Transaction failed: {get_transaction_data.result_xdr}")
