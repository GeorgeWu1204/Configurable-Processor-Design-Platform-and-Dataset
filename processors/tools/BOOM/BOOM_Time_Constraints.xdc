# Define the primary clock
create_clock -period 20.000 -name clock [get_ports serial_tl_0_clock_in]
create_clock -period 20.000 -name clock [get_ports clock_uncore]