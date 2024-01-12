import os
from signal import pause
import time

from gpiozero import Button, DistanceSensor, LED, Motor

from soroban import soroban_invoke

CONTRACT_HASH = os.getenv("CONTRACT_HASH")
ISSUER_ADDR_SECRET = os.getenv("ISSUER_ADDR_SECRET")
DISTRIBUTION_ADDR_SECRET = os.getenv("DISTRIBUTION_ADDR_SECRET")

if CONTRACT_HASH is None or ISSUER_ADDR_SECRET is None or DISTRIBUTION_ADDR_SECRET is None:
    raise ValueError(
        "Missing environment variables CONTRACT_HASH or ISSUER_ADDR_SECRET or DISTRIBUTION_ADDR_SECRET"
    )

# hardware setup
mint_button = Button(2)
burn_button = Button(26)

burn_led = LED(5)  # Red
mint_led = LED(6)  # Blue

motor = Motor(forward=4, backward=14)
d_sensor = DistanceSensor(23, 24)


def mint_token(n_token):
    mint_led.blink(on_time=0.25, off_time=0.25, n=4*5)
    speed = ...
    motor.forward()


def burn_token(n_token):
    burn_led.blink(on_time=0.25, off_time=0.25, n=4*5)
    speed = ...
    motor.backward()


def supply_check():
    dist = d_sensor.distance


while "Supply control":
    time.sleep(1)

    if ...:

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
