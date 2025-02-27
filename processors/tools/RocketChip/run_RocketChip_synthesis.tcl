open_project RocketChip_Prj.xpr
if { [llength $argv] < 1 } {
    puts "No incremental checkpoint identified, starting synthesis from scratch."
    # Remove any previous incremental checkpoint setting for a fresh start
    set_property incremental_checkpoint {} [get_runs synth_1]
} else {
    # Retrieve the config name argument
    set config_name [lindex $argv 0]

    set enable_incremental_synthesis 1

    # Define the path to the DCP file based on the config name
    set dcp_path "/home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/checkpoints/RocketChip/Synthesis/${config_name}.dcp"
    
    if { $enable_incremental_synthesis == 0 } {
        puts "Error: Incremental synthesis is disabled"
        exit 1
    } else {
        # Check if the specified DCP file exists
        if { ![file exists $dcp_path] } {
            puts "Error: Checkpoint file $dcp_path not found. Exiting."
            exit 1
        }
        
        # Add the DCP file to the project (ensuring no file duplication or conflict)
        add_files -fileset utils_1 -norecurse $dcp_path
        
        # Set incremental synthesis properties
        set_property STEPS.SYNTH_DESIGN.ARGS.INCREMENTAL_MODE aggressive [get_runs synth_1]
        set_property incremental_checkpoint $dcp_path [get_runs synth_1]
    }

}

# Clear All the Generated Files
remove_files [get_files *]
# Add the Verilog files
add_files [glob /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/chipyard/sims/verilator/generated-src/*]
# Disable the unnecessary files
set_property is_enabled false [get_files  /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/chipyard/sims/verilator/generated-src/chipyard.harness.TestHarness.CustomisedRocketConfig/gen-collateral/ClockSourceAtFreqMHz.v]
set_property is_enabled false [get_files  /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/chipyard/sims/verilator/generated-src/chipyard.harness.TestHarness.CustomisedRocketConfig/gen-collateral/SimTSI.v]
set_property is_enabled false [get_files  {/home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/chipyard/sims/verilator/generated-src/chipyard.harness.TestHarness.CustomisedRocketConfig/gen-collateral/SimUART.v /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/chipyard/sims/verilator/generated-src/chipyard.harness.TestHarness.CustomisedRocketConfig/gen-collateral/SimJTAG.v /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/chipyard/sims/verilator/generated-src/chipyard.harness.TestHarness.CustomisedRocketConfig/gen-collateral/SimDRAM.v}]
set_property is_enabled false [get_files  /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/chipyard/sims/verilator/generated-src/chipyard.harness.TestHarness.CustomisedRocketConfig/gen-collateral/TestDriver.v]
# Set Clock Constraints
add_files -fileset constrs_1 -norecurse /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/tools/RocketChip/Rocket_Chip_Time_Constraints.xdc
# Set the Top Module
set_property top DigitalTop [current_fileset]

reset_run synth_1
launch_runs synth_1 -jobs 12
wait_on_run synth_1
open_run synth_1 -name synth_1
report_utilization -file ../../Logs/Syn_Report/RocketChip_utilization_synth.rpt
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 10 -input_pins -routable_nets -name timing_1 -file ../../Logs/Syn_Report/RocketChip_timing_synth.rpt
report_power -file ../../Logs/Syn_Report/RocketChip_power_synth.rpt
close_project