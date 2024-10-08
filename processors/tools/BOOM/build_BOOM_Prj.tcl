create_project BOOM_Prj /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/Vivado_Prj/BOOM_Prj -part xczu19eg-ffvc1760-2-i
set_property top ChipTop [current_fileset]
add_files -fileset constrs_1 -norecurse /home/hw1020/Documents/Configurable-Processor-Design-Platform-and-Dataset/processors/tools/BOOM/BOOM_Time_Constraints.xdc