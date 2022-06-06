SHELL := /bin/bash
.PHONY: run
export PYTHONPATH=.

run:
	python src/main.py
