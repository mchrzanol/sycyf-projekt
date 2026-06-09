module voter6 (
    input  wire        aclk,
    input  wire        aresetn,
    input  wire [1:0]  s_axis_tdata,
    input  wire        s_axis_tvalid,
    output wire        s_axis_tready,
    output reg  [1:0]  cmd_out,
    output reg         cmd_valid
);

  localparam MIN_VOTES = 3'd4;

  reg [1:0] shift_reg [0:5];
  reg [2:0] frame_cnt;
  reg [1:0] last_cmd;

  reg [2:0] count [0:3];
  reg [1:0] winner;
  integer k;

  always @(posedge aclk) begin
    if (!aresetn) begin
      for (k = 0; k < 6; k = k + 1) shift_reg[k] <= 2'b00;
      frame_cnt <= 3'd0;
      last_cmd  <= 2'b00;
      cmd_out   <= 2'b00;
      cmd_valid <= 1'b0;
    end else if (s_axis_tvalid && s_axis_tready) begin
      for (k = 5; k > 0; k = k - 1) shift_reg[k] <= shift_reg[k-1];
      shift_reg[0] <= s_axis_tdata;
      frame_cnt <= frame_cnt + 1;

      if (frame_cnt == 3'd5) begin
        frame_cnt <= 3'd0;
        if (count[winner] >= MIN_VOTES) begin
          cmd_out   <= winner;
          cmd_valid <= 1'b1;
        end else begin
          cmd_out   <= last_cmd;
          cmd_valid <= 1'b0;
        end
        last_cmd <= cmd_out;
      end else begin
        cmd_valid <= 1'b0;
      end
    end else begin
      cmd_valid <= 1'b0;
    end
  end

  always @(*) begin
    for (k = 0; k < 4; k = k + 1) count[k] = 3'd0;
    for (k = 0; k < 6; k = k + 1)
      count[shift_reg[k]] = count[shift_reg[k]] + 1;

    winner = last_cmd;
    if (count[0] > count[winner]) winner = 2'd0;
    if (count[1] > count[winner]) winner = 2'd1;
    if (count[2] > count[winner]) winner = 2'd2;
    if (count[3] > count[winner]) winner = 2'd3;
  end

  assign s_axis_tready = 1'b1;

endmodule
