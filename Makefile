SHELL := /bin/bash

CHIPYARD_DIR :=./processors/chipyard
SIM_DIR :=./processors/chipyard/sims/verilator
VIVADO_DIR :=./processors/Vivado_Prj

initial:
	@echo "Sourcing env.sh from $(CHIPYARD_DIR)"
	@source $(CHIPYARD_DIR)/env.sh && echo "env.sh sourced successfully."


test_boom:
	@echo "Running tests for BOOM"
	@cd src; bash ../experiments/scripts/boom_test.sh

test_boom_BO:
	@echo "Running tests for processor design framework for BOOM"
	@cd src; bash ../experiments/scripts/boom_test_BO.sh

test_rocket:
	@echo "Running tests for Rocket"
	@cd src; bash ../experiments/scripts/rocket_test.sh

test_rocket_BO:
	@echo "Running tests for processor design framework for Rocket"
	@cd src; bash ../experiments/scripts/rocket_test_BO.sh

analyse_rocket:
	@echo "Analyzing Rocket"
	@cd src; bash ../experiments/scripts/rocket_analyse_weights.sh

clean:
	make -C $(SIM_DIR) clean

clean_vivado_log:
	@echo "Cleaning up .jou and .log files in $(VIVADO_DIR)"
	@find $(VIVADO_DIR) -type f \( -name '*.jou' -o -name '*.log' -o -name '*.str' \) -exec rm -f {} +
	@echo "Cleanup complete."

.PHONY: clean clean_vivado_log test_boom test_rocket test_boom_BO test_rocket_BO analyse_rocket