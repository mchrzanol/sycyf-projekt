module feature_extractor (
    input  wire        aclk,
    input  wire        aresetn,
    input  wire [63:0] s_axis_tdata,
    input  wire        s_axis_tvalid,
    output wire        s_axis_tready,
    output reg  [94:0] m_axis_tdata,
    output reg         m_axis_tvalid,
    input  wire        m_axis_tready
);

  wire [7:0] row [0:7];
  genvar r;
  generate
    for (r = 0; r < 8; r = r + 1) begin : g_rows
      assign row[r] = s_axis_tdata[8*r +: 8];
    end
  endgenerate

  function [3:0] popcount8;
    input [7:0] v;
    begin
      popcount8 = v[0] + v[1] + v[2] + v[3]
                + v[4] + v[5] + v[6] + v[7];
    end
  endfunction

  reg [3:0] row_sum [0:7];
  reg [3:0] col_sum [0:7];
  reg [6:0] total;
  reg [4:0] cm_x, cm_y;
  integer   i, j;

  reg [7:0] inv_lut [1:64];
  initial $readmemh("inv_lut.hex", inv_lut);

  reg [9:0] sum_x, sum_y;

  always @(posedge aclk) begin
    if (!aresetn) begin
      m_axis_tvalid <= 1'b0;
      total <= 7'd0;
      sum_x <= 10'd0;
      sum_y <= 10'd0;
    end else if (s_axis_tvalid && s_axis_tready) begin
      for (i = 0; i < 8; i = i + 1)
        row_sum[i] <= popcount8(row[i]);
      for (j = 0; j < 8; j = j + 1)
        col_sum[j] <= s_axis_tdata[0*8+j] + s_axis_tdata[1*8+j]
                    + s_axis_tdata[2*8+j] + s_axis_tdata[3*8+j]
                    + s_axis_tdata[4*8+j] + s_axis_tdata[5*8+j]
                    + s_axis_tdata[6*8+j] + s_axis_tdata[7*8+j];

      total <= popcount8(row[0]) + popcount8(row[1])
             + popcount8(row[2]) + popcount8(row[3])
             + popcount8(row[4]) + popcount8(row[5])
             + popcount8(row[6]) + popcount8(row[7]);

      sum_x <= (s_axis_tdata[ 0] + s_axis_tdata[ 8] + s_axis_tdata[16] + s_axis_tdata[24]
              + s_axis_tdata[32] + s_axis_tdata[40] + s_axis_tdata[48] + s_axis_tdata[56]) * 4'd0
             + (s_axis_tdata[ 1] + s_axis_tdata[ 9] + s_axis_tdata[17] + s_axis_tdata[25]
              + s_axis_tdata[33] + s_axis_tdata[41] + s_axis_tdata[49] + s_axis_tdata[57]) * 4'd1
             + (s_axis_tdata[ 2] + s_axis_tdata[10] + s_axis_tdata[18] + s_axis_tdata[26]
              + s_axis_tdata[34] + s_axis_tdata[42] + s_axis_tdata[50] + s_axis_tdata[58]) * 4'd2
             + (s_axis_tdata[ 3] + s_axis_tdata[11] + s_axis_tdata[19] + s_axis_tdata[27]
              + s_axis_tdata[35] + s_axis_tdata[43] + s_axis_tdata[51] + s_axis_tdata[59]) * 4'd3
             + (s_axis_tdata[ 4] + s_axis_tdata[12] + s_axis_tdata[20] + s_axis_tdata[28]
              + s_axis_tdata[36] + s_axis_tdata[44] + s_axis_tdata[52] + s_axis_tdata[60]) * 4'd4
             + (s_axis_tdata[ 5] + s_axis_tdata[13] + s_axis_tdata[21] + s_axis_tdata[29]
              + s_axis_tdata[37] + s_axis_tdata[45] + s_axis_tdata[53] + s_axis_tdata[61]) * 4'd5
             + (s_axis_tdata[ 6] + s_axis_tdata[14] + s_axis_tdata[22] + s_axis_tdata[30]
              + s_axis_tdata[38] + s_axis_tdata[46] + s_axis_tdata[54] + s_axis_tdata[62]) * 4'd6
             + (s_axis_tdata[ 7] + s_axis_tdata[15] + s_axis_tdata[23] + s_axis_tdata[31]
              + s_axis_tdata[39] + s_axis_tdata[47] + s_axis_tdata[55] + s_axis_tdata[63]) * 4'd7;

      sum_y <= popcount8(row[0]) * 4'd0
             + popcount8(row[1]) * 4'd1
             + popcount8(row[2]) * 4'd2
             + popcount8(row[3]) * 4'd3
             + popcount8(row[4]) * 4'd4
             + popcount8(row[5]) * 4'd5
             + popcount8(row[6]) * 4'd6
             + popcount8(row[7]) * 4'd7;

      m_axis_tvalid <= 1'b1;
    end else if (m_axis_tvalid && m_axis_tready) begin
      m_axis_tvalid <= 1'b0;
    end
  end

  wire [17:0] cmx_full = sum_x * inv_lut[(total == 0) ? 1 : total];
  wire [17:0] cmy_full = sum_y * inv_lut[(total == 0) ? 1 : total];
  always @(posedge aclk) begin
    cm_x <= (total == 0) ? 5'd14 : cmx_full[12:8];
    cm_y <= (total == 0) ? 5'd14 : cmy_full[12:8];
  end

  always @(*) begin
    for (i = 0; i < 8; i = i + 1) begin
      m_axis_tdata[5*i      +: 5] = {1'b0, row_sum[i]};
      m_axis_tdata[5*(i+8)  +: 5] = {1'b0, col_sum[i]};
    end
    m_axis_tdata[5*16 +: 5] = cm_x;
    m_axis_tdata[5*17 +: 5] = cm_y;
    m_axis_tdata[5*18 +: 5] = total[6:2];
  end

  assign s_axis_tready = ~m_axis_tvalid | m_axis_tready;

endmodule
