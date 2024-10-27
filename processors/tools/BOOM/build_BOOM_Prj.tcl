create_project BOOM_Prj /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/Vivado_Prj/BOOM_Prj -part xczu19eg-ffvc1760-2-i
set_property top ChipTop [current_fileset]
add_files -fileset constrs_1 -norecurse /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/tools/BOOM/BOOM_Time_Constraints.xdc
set_property AUTO_INCREMENTAL_CHECKPOINT 1 [get_runs synth_1]
set_property AUTO_INCREMENTAL_CHECKPOINT.DIRECTORY /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/checkpoints/BOOM/Synthesis/synth_1 [get_runs synth_1]
set_property STEPS.SYNTH_DESIGN.ARGS.INCREMENTAL_MODE aggressive [get_runs synth_1]