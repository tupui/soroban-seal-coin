.PHONY: help install run
.DEFAULT_GOAL := help
SHELL:=/bin/bash

ifndef CONTRACT_HASH
   override CONTRACT_HASH = "..."
endif

ifndef ISSUER_ADDR_SECRET
   override ISSUER_ADDR_SECRET = ...
endif

# Add help text after each target name starting with '\#\#'
help:   ## show this help
	@echo -e "Help for this makefile\n"
	@echo "Possible commands are:"
	@grep -h "##" $(MAKEFILE_LIST) | grep -v grep | sed -e 's/\(.*\):.*##\(.*\)/    \1: \2/'

install:  ## install Python dependencies
	# Python part
	python -m venv venv
	source venv/bin/activate
	pip install .

run:
	source venv/bin/activate && \
	CONTRACT_HASH=$(CONTRACT_HASH) ISSUER_ADDR_SECRET=$(ISSUER_ADDR_SECRET) python seal_coin_supply.py
