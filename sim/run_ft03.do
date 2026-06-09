vlog -quiet ../hdl/feature_extractor.v
vlog -quiet ../hdl/weight_rom.v
vlog -quiet ../hdl/classifier_mlp.v
vlog -quiet ../hdl/voter6.v
vlog -quiet ../hdl/ctrl_top.v
vlog -quiet ../hdl/system_top.v
vlog -quiet ../tb/tb_system_top.v

vsim -G TEST_SCENARIO=3 work.tb_system_top

add wave -divider "Clock & Reset"
add wave /tb_system_top/aclk
add wave /tb_system_top/aresetn
add wave -divider "Input"
add wave -radix hex /tb_system_top/s_axis_tdata
add wave /tb_system_top/s_axis_tvalid
add wave -divider "Layer 2 output"
add wave -radix binary /tb_system_top/dut/l2_out
add wave -divider "Voter"
add wave -radix unsigned /tb_system_top/dut/voter_inst/count
add wave -radix binary /tb_system_top/dut/cmd_out
add wave /tb_system_top/dut/cmd_valid

run 200us
