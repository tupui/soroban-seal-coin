import datetime
import logging
import math
import os
import statistics
import time
from typing import Literal

from gpiozero import Button, DistanceSensor, LED, Motor
import stellar_sdk
from stellar_sdk.exceptions import SdkError

import sii
from screen import screen
from soroban import soroban_invoke


logging.basicConfig(level=logging.INFO)


CONTRACT_HASH = os.getenv("CONTRACT_HASH")
ISSUER_ADDR_SECRET = os.getenv("ISSUER_ADDR_SECRET")
DISTRIBUTION_ADDR_SECRET = os.getenv("DISTRIBUTION_ADDR_SECRET")

issuer_kp = stellar_sdk.Keypair.from_secret(ISSUER_ADDR_SECRET)
distribution_kp = stellar_sdk.Keypair.from_secret(DISTRIBUTION_ADDR_SECRET)
stellar_server = stellar_sdk.Server(horizon_url="https://horizon-testnet.stellar.org")

# if CONTRACT_HASH is None or ISSUER_ADDR_SECRET is None or DISTRIBUTION_ADDR_SECRET is None:
#     raise ValueError(
#         "Missing environment variables CONTRACT_HASH or ISSUER_ADDR_SECRET"
#         " or DISTRIBUTION_ADDR_SECRET"
#     )

# SEAL setup
# 1_000_000_000 SEAL = 1 l
TOKEN_GENESIS = 1_000_000_000
LITER_PER_TOKEN = 1e-9
TOKEN_VOLATILE = 500_000_000

# hardware setup
mint_button = Button(2)
burn_button = Button(26)
MINT_AMOUNT = 100_000_000
BURN_AMOUNT = 100_000_000

burn_led = LED(5)  # Red
mint_led = LED(6)  # Blue

pump = Motor(forward=4, backward=14)
FLOW_RATE = 0.0015  # l/s

d_sensor = DistanceSensor(23, 24)
SURFACE_CONTAINER = math.pi * 0.01**2  # m^2


def token_control(n_token: int, operation: Literal["mint", "burn"]) -> None:
    """Mint or burn `n_token` by pumping in/out.

    Parameters
    ----------
    n_token : int
        Number of token.
    operation : {"mint", "burn"}
        Mint or burn token.
    """
    if operation == "mint":
        led = mint_led
        pump_run = pump.forward
    else:
        led = burn_led
        pump_run = pump.backward

    vol = n_token * LITER_PER_TOKEN  # l
    pump_time = vol / FLOW_RATE  # s

    led.blink(on_time=0.25, off_time=0.25, n=2 * max(2, int(pump_time)))
    pump_run(1)
    time.sleep(pump_time)
    pump.stop()


def supply_offchain() -> int:
    """Proof of reserve by checking the liquid level. Referred as off-chain."""
    dists = []
    for _ in range(100):
        dists.append(d_sensor.distance)
        time.sleep(0.01)
    dist = statistics.median(dists)  # m
    vol = SURFACE_CONTAINER * dist  # m^3
    n_token = math.floor(vol / LITER_PER_TOKEN)
    return n_token


def supply_onchain() -> int:
    """On-chain available supply."""
    account = stellar_server.load_account(distribution_kp.public_key)
    balances = account.raw_data["balances"]
    seal_onchain = [
        asset["balance"]
        for asset in balances
        if "asset_code" in asset and asset["asset_code"] == "SEAL"
    ]
    try:
        seal_onchain = int(seal_onchain[0])
    except IndexError:
        seal_onchain = 0
    return seal_onchain


# Special Mint and Burn event
mint_button.when_activated = lambda x: token_control(
    n_token=MINT_AMOUNT, operation="mint"
)
burn_button.when_activated = lambda x: token_control(
    n_token=BURN_AMOUNT, operation="burn"
)

doy_last_executed = 0
while "SEAL management":
    print("-----------------")
    today_date = datetime.datetime.now(tz=datetime.timezone.utc)
    doy = today_date.timetuple().tm_yday

    doy_oracle, extent_oracle = sii.daily_sea_ice_extent()
    # convert to int but keep 3 digit precision
    # 13.976 -> 13976
    extent_oracle = int(extent_oracle * 1000)
    delta = extent_oracle - sii.MEDIAN_EXTENT[doy - 1]

    print(f"It's a beautiful day: {today_date.strftime('%Y-%m-%d')}")
    seal_offchain = supply_offchain()
    print(f"Current supply: {seal_offchain}")

    print(f"DOY extent: {extent_oracle}")

    # only execute if measurement is from current DOY and only once per day
    if (doy == doy_oracle) and (doy_oracle != doy_last_executed):
        # convert delta extent to token amount e.g.
        # sea_ice_extent = 13976, MEDIAN_EXTENT = 14526
        # 13976-14526 = -550
        # -550 * 100 = -55k SEAL
        amount = int(delta * 100)

        new_supply = seal_offchain + amount
        if not (
            TOKEN_GENESIS - TOKEN_VOLATILE < new_supply < TOKEN_GENESIS + TOKEN_VOLATILE
        ):
            logging.warning(f"New supply would be too much or too little: {new_supply}")
            continue

        # only trigger if outside [-1000,1000]
        if amount > 1000:
            print("There is more ice than usual, Seals will be happy! Minting token")
            token_control(amount, "mint")
        elif amount < -1000:
            print("Ice is melting faster, poo Seals! Burning token")
            token_control(amount, "burn")

        seal_offchain = supply_offchain()
        print(f"New supply: {seal_offchain}")

        # calling Soroban smart contract
        try:
            # fn correct_supply(
            #     env: &Env, issuer: Address, distributor: Address,
            #     doy: u32, sea_ice_extent: u32
            # )
            args = [
                # issuer
                stellar_sdk.scval.to_address(issuer_kp.public_key),
                # distributor
                stellar_sdk.scval.to_address(distribution_kp.public_key),
                # doy
                stellar_sdk.scval.to_int32(doy),
                # sea_ice_extent
                stellar_sdk.scval.to_int32(extent_oracle),
            ]
            result = soroban_invoke(
                secret_key=ISSUER_ADDR_SECRET,
                contract_id=CONTRACT_HASH,
                function_name="correct_supply",
                args=args,
            )
        except SdkError as ex:
            logging.error(ex)
        else:
            # mark as executed only if no error with Soroban
            doy_last_executed = doy

    seal_onchain = supply_onchain()

    epd = screen.SealScreen()
    epd.update_screen(
        seal_onchain=seal_onchain,
        seal_offchain=seal_offchain,
        ice_extent=extent_oracle,
        delta=delta,
    )

    time.sleep(3600)
