# ============================================================
# build.tcl -- Vivado batch build script for SYCYF project
# Target: Xilinx Artix-7 XC7A35T-1CPG236C (Digilent Basys 3)
# Usage:  vivado -mode batch -source build.tcl
# ============================================================

set proj_name  "sycyf_projekt"
set proj_dir   "./vivado_build"
set part       "xc7a35tcpg236-1"
set top_module "system_top"

# -- Create project -------------------------------------------
create_project $proj_name $proj_dir -part $part -force

# -- Add HDL sources -----------------------------------------
add_files -norecurse [glob hdl/*.v]
set_property top $top_module [current_fileset]

# -- Add data files (weight ROM hex, LUT hex) -----------------
add_files -norecurse inv_lut.hex

# -- Generate constraints (XDC) inline ------------------------
set xdc_file "$proj_dir/basys3.xdc"
set fp [open $xdc_file w]
puts $fp "## Clock signal (Basys 3 - 100 MHz)"
puts $fp "set_property -dict { PACKAGE_PIN W5 IOSTANDARD LVCMOS33 } \[get_ports aclk\]"
puts $fp "create_clock -add -name sys_clk -period 10.00 -waveform {0 5} \[get_ports aclk\]"
puts $fp ""
puts $fp "## Reset (active low) - center button"
puts $fp "set_property -dict { PACKAGE_PIN U18 IOSTANDARD LVCMOS33 } \[get_ports aresetn\]"
puts $fp ""
puts $fp "## Configuration"
puts $fp "set_property CFGBVS VCCO \[current_design\]"
puts $fp "set_property CONFIG_VOLTAGE 3.3 \[current_design\]"
close $fp
add_files -fileset constrs_1 -norecurse $xdc_file

# -- Update compile order ------------------------------------
update_compile_order -fileset sources_1

# -- Synthesis ------------------------------------------------
launch_runs synth_1 -jobs 4
wait_on_run synth_1
open_run synth_1

# -- Reports post-synthesis -----------------------------------
report_utilization -file "$proj_dir/post_synth_util.rpt"

# -- Implementation (Performance_Explore) ---------------------
set_property strategy Performance_Explore [get_runs impl_1]
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
open_run impl_1

# -- Reports post-implementation ------------------------------
report_utilization -file "$proj_dir/post_impl_util.rpt"
report_timing_summary -file "$proj_dir/post_impl_timing.rpt"

# -- Done -----------------------------------------------------
puts "============================================"
puts " Build complete. Reports in $proj_dir/"
puts "============================================"
