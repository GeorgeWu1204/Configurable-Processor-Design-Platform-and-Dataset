SHELL := /bin/bash

CHIPYARD_DIR :=./processors/chipyard
SIM_DIR :=./processors/chipyard/sims/verilator

initial:
	@echo "Sourcing env.sh from $(CHIPYARD_DIR)"
	@source $(CHIPYARD_DIR)/env.sh && echo "env.sh sourced successfully."


test_boom:
	@echo "Running tests for BOOM"
	@cd src; bash scripts/boom_test.sh

test_boom_BO:
	@echo "Running tests for processor design framework for BOOM"
	@cd src; bash scripts/boom_test_BO.sh

test_rocket:
	@echo "Running tests for Rocket"
	@cd src; bash scripts/rocket_test.sh

test_rocket_BO:
	@echo "Running tests for processor design framework for Rocket"
	@cd src; bash scripts/rocket_test_BO.sh

analyse_rocket:
	@echo "Analyzing Rocket"
	@cd src; bash scripts/rocket_analyse_weights.sh

clean:
	make -C $(SIM_DIR) clean