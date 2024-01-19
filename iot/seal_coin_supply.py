import os
import math
from signal import pause
import statistics
import time
from typing import Literal

from gpiozero import Button, DistanceSensor, LED, Motor

from soroban import soroban_invoke

CONTRACT_HASH = os.getenv("CONTRACT_HASH")
ISSUER_ADDR_SECRET = os.getenv("ISSUER_ADDR_SECRET")
DISTRIBUTION_ADDR_SECRET = os.getenv("DISTRIBUTION_ADDR_SECRET")

if CONTRACT_HASH is None or ISSUER_ADDR_SECRET is None or DISTRIBUTION_ADDR_SECRET is None:
    raise ValueError(
        "Missing environment variables CONTRACT_HASH or ISSUER_ADDR_SECRET or DISTRIBUTION_ADDR_SECRET"
    )

# 1_000_000_000 SEAL = 0.1 l
TOKEN_VOL = 1e-10

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
SURFACE_CONTAINER = math.pi*0.01**2  # m^2


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

    vol = n_token * TOKEN_VOL  # l
    pump_time = vol / FLOW_RATE  # s

    led.blink(on_time=0.25, off_time=0.25, n=2*max(2, int(pump_time)))
    pump_run(1)
    time.sleep(pump_time)
    pump.stop()


def supply_check() -> int:
    """Proof of reserve by checking the liquid level."""
    dists = []
    for _ in range(100):
        dists.append(d_sensor.distance)
        time.sleep(0.01)
    dist = statistics.median(dists)  # m
    vol = SURFACE_CONTAINER * dist  # m^3
    n_token = math.floor(vol / TOKEN_VOL)
    return n_token


# Special Mint and Burn event
mint_button.when_activated = lambda x: token_control(n_token=MINT_AMOUNT, operation="mint")
burn_button.when_activated = lambda x: token_control(n_token=BURN_AMOUNT, operation="burn")


while "Oracle":
    time.sleep(1)

    #print("-----------------")

    print(f"Supply: {supply_check()}")
    # print("Minting")
    # token_control(MINT_AMOUNT, "mint")
    #
    # print(f"Supply: {supply_check()}")
    #
    # print("Burning hot")
    # token_control(BURN_AMOUNT, "burn")
    #
    # print(f"Supply: {supply_check()}")

    if False:

        print("Calling Soroban smart contract")
        result = soroban_invoke(
            secret_key=ISSUER_ADDR_SECRET,
            contract_id=CONTRACT_HASH,
            function_name=...,
            args=...,
        )

        if result is not None:
            print("Contract called successfully!")
        break

pause()
