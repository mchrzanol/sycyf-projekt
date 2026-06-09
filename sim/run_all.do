quietly set pass_count 0
quietly set fail_count 0
quietly set total_tests 7

vlog -quiet ../hdl/feature_extractor.v
vlog -quiet ../hdl/weight_rom.v
vlog -quiet ../hdl/classifier_mlp.v
vlog -quiet ../hdl/voter6.v
vlog -quiet ../hdl/ctrl_top.v
vlog -quiet ../hdl/system_top.v
vlog -quiet ../tb/tb_system_top.v

proc run_test {test_name define_name sim_time} {
    global pass_count fail_count
    puts "--- Running $test_name ---"
    vsim -quiet -G TEST_SCENARIO=$define_name work.tb_system_top
    run $sim_time
    if {[examine -radix ascii /tb_system_top/test_result] eq "PASS"} {
        puts ">>> $test_name: PASS"
        incr pass_count
    } else {
        puts ">>> $test_name: FAIL"
        incr fail_count
    }
    quit -sim
}

run_test "FT-01 (nominal)"       1  "200us"
run_test "FT-02 (working cond.)" 2  "1ms"
run_test "FT-03 (fail-safe)"     3  "200us"
run_test "FT-04 (edge shift)"    4  "1ms"
run_test "FT-05 (max noise)"     5  "1ms"
run_test "FT-06 (backpressure)"  6  "1.5ms"
run_test "FT-07 (reset)"         7  "100us"

puts "============================================"
puts "=== SUMMARY: $pass_count/$total_tests tests PASSED ==="
puts "============================================"

quit -f
