.PHONY: help prepare install run
.DEFAULT_GOAL := help
SHELL:=/bin/bash

ifndef CONTRACT_HASH
   override CONTRACT_HASH = "..."
endif

# Add help text after each target name starting with '\#\#'
help:   ## show this help
	@echo -e "Help for this makefile\n"
	@echo "Possible commands are:"
	@grep -h "##" $(MAKEFILE_LIST) | grep -v grep | sed -e 's/\(.*\):.*##\(.*\)/    \1: \2/'

prepare:  # activate SPI interface for e-ink display
	sudo raspi-config
	# Choose Interfacing Options -> SPI -> Yes Enable SPI interface
	# sudo reboot

install:  ## install Python dependencies
	# Python part
	python -m venv venv
	source venv/bin/activate
	pip install .

run:  ## run the supply controller script
	source venv/bin/activate && \
	CONTRACT_HASH=$(CONTRACT_HASH) python seal_coin_supply.py
