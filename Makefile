SHELL := /bin/bash
.PHONY: run
export PYTHONPATH=.

run:
	python3 src/run.py
