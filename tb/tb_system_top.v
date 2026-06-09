`timescale 1ns / 1ps

module tb_system_top;

  parameter TEST_SCENARIO = 1;
  parameter CLK_PERIOD    = 10;

  reg         aclk;
  reg         aresetn;
  reg  [63:0] s_axis_tdata;
  reg         s_axis_tvalid;
  wire        s_axis_tready;
  wire [1:0]  cmd_out;
  wire        cmd_valid;

  reg [7:0] test_result;

  system_top dut (
      .aclk           (aclk),
      .aresetn        (aresetn),
      .s_axis_tdata   (s_axis_tdata),
      .s_axis_tvalid  (s_axis_tvalid),
      .s_axis_tready  (s_axis_tready),
      .cmd_out        (cmd_out),
      .cmd_valid      (cmd_valid)
  );

  always #(CLK_PERIOD/2) aclk = ~aclk;

  reg [63:0] frame_mem  [0:16383];
  reg [3:0]  exp_mem    [0:4095];
  integer    n_frames, n_symbols;
  integer    symbol_id;
  integer    frame_id;
  integer    n_ok, n_err, n_held;
  integer    window_frame;

  reg [255:0] frame_file;
  reg [255:0] exp_file;

  initial begin
    aclk          = 0;
    aresetn       = 0;
    s_axis_tdata  = 64'd0;
    s_axis_tvalid = 1'b0;
    test_result   = "F";

    case (TEST_SCENARIO)
      1: begin frame_file = "vectors/ft01_frames.txt"; exp_file = "vectors/ft01_decisions.txt"; n_symbols = 200;  end
      2: begin frame_file = "vectors/ft02_frames.txt"; exp_file = "vectors/ft02_decisions.txt"; n_symbols = 1000; end
      3: begin frame_file = "vectors/ft03_frames.txt"; exp_file = "vectors/ft03_decisions.txt"; n_symbols = 100;  end
      4: begin frame_file = "vectors/ft04_frames.txt"; exp_file = "vectors/ft04_decisions.txt"; n_symbols = 1000; end
      5: begin frame_file = "vectors/ft05_frames.txt"; exp_file = "vectors/ft05_decisions.txt"; n_symbols = 1000; end
      6: begin frame_file = "vectors/ft06_frames.txt"; exp_file = "vectors/ft06_decisions.txt"; n_symbols = 1000; end
      7: begin frame_file = "vectors/ft07_frames.txt"; exp_file = "vectors/ft07_decisions.txt"; n_symbols = 20;   end
    endcase

    n_frames = n_symbols * 6;
    $readmemb(frame_file, frame_mem);
    $readmemh(exp_file, exp_mem);

    #(CLK_PERIOD * 5);
    aresetn = 1;
    #(CLK_PERIOD * 2);

    n_ok   = 0;
    n_err  = 0;
    n_held = 0;
    symbol_id   = 0;
    window_frame = 0;

    for (frame_id = 0; frame_id < n_frames; frame_id = frame_id + 1) begin
      s_axis_tdata  = frame_mem[frame_id];
      s_axis_tvalid = 1'b1;

      if (TEST_SCENARIO == 6 && ($random % 100) < 30) begin
        s_axis_tvalid = 1'b0;
        @(posedge aclk);
        s_axis_tvalid = 1'b1;
      end

      @(posedge aclk);
      while (!s_axis_tready) @(posedge aclk);
      s_axis_tvalid = 1'b0;

      @(posedge aclk);
      while (!cmd_valid && window_frame == 5) begin
        @(posedge aclk);
      end

      window_frame = window_frame + 1;
      if (window_frame == 6) begin
        window_frame = 0;
        if (!cmd_valid) begin
          n_held = n_held + 1;
          $display("[%0t] sym %0d: HELD (no clear majority)", $time, symbol_id);
        end else if (cmd_out === exp_mem[symbol_id][1:0]) begin
          n_ok = n_ok + 1;
        end else begin
          n_err = n_err + 1;
          $display("[%0t] sym %0d: MISMATCH got=%b exp=%b",
                   $time, symbol_id, cmd_out, exp_mem[symbol_id][1:0]);
        end
        symbol_id = symbol_id + 1;
      end

      #(CLK_PERIOD);
    end

    #(CLK_PERIOD * 20);

    $display("RESULT: ok=%0d err=%0d held=%0d", n_ok, n_err, n_held);

    case (TEST_SCENARIO)
      1: if (n_ok == n_symbols)                         begin test_result = "P"; $display(">>> TEST PASS"); end
         else                                           begin $display(">>> TEST FAIL"); end
      2: if (n_ok >= (n_symbols * 90 / 100))            begin test_result = "P"; $display(">>> TEST PASS"); end
         else                                           begin $display(">>> TEST FAIL"); end
      3: if (n_held >= (n_symbols * 90 / 100))          begin test_result = "P"; $display(">>> TEST PASS"); end
         else                                           begin $display(">>> TEST FAIL"); end
      4: begin test_result = "P"; $display(">>> TEST PASS (informational)"); end
      5: begin test_result = "P"; $display(">>> TEST PASS (informational)"); end
      6: if (n_ok >= (n_symbols * 90 / 100))            begin test_result = "P"; $display(">>> TEST PASS"); end
         else                                           begin $display(">>> TEST FAIL"); end
      7: if (n_ok == n_symbols)                         begin test_result = "P"; $display(">>> TEST PASS"); end
         else                                           begin $display(">>> TEST FAIL"); end
    endcase

    $finish;
  end

endmodule
