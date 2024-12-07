# Define the primary clock
create_clock -period 20.000 -name clock [get_ports auto_chipyard_prcictrl_domain_reset_setter_clock_in_member_allClocks_uncore_clock]
