module classifier_mlp (
    input  wire         aclk,
    input  wire         aresetn,
    input  wire [94:0]  s_axis_tdata,
    input  wire         s_axis_tvalid,
    output wire         s_axis_tready,
    output reg  [1:0]   m_axis_tdata,
    output reg          m_axis_tvalid,
    input  wire         m_axis_tready,
    output reg  [8:0]   rom_addr,
    input  wire [7:0]   rom_dout
);

  localparam S_IDLE    = 3'd0,
             S_HIDDEN  = 3'd1,
             S_BIAS_H  = 3'd2,
             S_OUTPUT  = 3'd3,
             S_BIAS_O  = 3'd4,
             S_ARGMAX  = 3'd5,
             S_DONE    = 3'd6;

  reg [2:0] state;
  reg [4:0] mac_cnt;
  reg [3:0] neuron_id;

  reg signed [7:0] feature [0:18];
  reg signed [15:0] acc;
  reg signed [7:0] hidden_out [0:15];
  reg signed [15:0] logit [0:3];

  integer k;

  always @(posedge aclk) begin
    if (state == S_IDLE && s_axis_tvalid && s_axis_tready) begin
      for (k = 0; k < 19; k = k + 1)
        feature[k] <= {3'b000, s_axis_tdata[5*k +: 5]};
    end
  end

  always @(posedge aclk) begin
    if (!aresetn) begin
      state         <= S_IDLE;
      m_axis_tvalid <= 1'b0;
      mac_cnt       <= 5'd0;
      neuron_id     <= 4'd0;
      acc           <= 16'sd0;
      rom_addr      <= 9'd0;
    end else begin
      case (state)
        S_IDLE: begin
          m_axis_tvalid <= 1'b0;
          if (s_axis_tvalid && s_axis_tready) begin
            state     <= S_HIDDEN;
            mac_cnt   <= 5'd0;
            neuron_id <= 4'd0;
            acc       <= 16'sd0;
            rom_addr  <= 9'd0;
          end
        end

        S_HIDDEN: begin
          if (mac_cnt < 5'd19) begin
            acc     <= acc + $signed(feature[mac_cnt]) * $signed(rom_dout);
            mac_cnt <= mac_cnt + 1;
            rom_addr <= rom_addr + 1;
          end else begin
            state    <= S_BIAS_H;
            rom_addr <= 9'd304 + {5'd0, neuron_id};
          end
        end

        S_BIAS_H: begin
          begin
            reg signed [15:0] acc_biased;
            acc_biased = acc + {{8{rom_dout[7]}}, rom_dout};
            hidden_out[neuron_id] <= (acc_biased[15] == 1'b0)
                                   ? acc_biased[11:4]
                                   : 8'sd0;
          end
          acc <= 16'sd0;
          mac_cnt <= 5'd0;
          if (neuron_id < 4'd15) begin
            neuron_id <= neuron_id + 1;
            rom_addr  <= 9'd0 + ({5'd0, neuron_id} + 1) * 19;
            state     <= S_HIDDEN;
          end else begin
            neuron_id <= 4'd0;
            rom_addr  <= 9'd320;
            state     <= S_OUTPUT;
          end
        end

        S_OUTPUT: begin
          if (mac_cnt < 5'd16) begin
            acc     <= acc + $signed(hidden_out[mac_cnt]) * $signed(rom_dout);
            mac_cnt <= mac_cnt + 1;
            rom_addr <= rom_addr + 1;
          end else begin
            state    <= S_BIAS_O;
            rom_addr <= 9'd384 + {5'd0, neuron_id};
          end
        end

        S_BIAS_O: begin
          logit[neuron_id] <= acc + {{8{rom_dout[7]}}, rom_dout};
          acc <= 16'sd0;
          mac_cnt <= 5'd0;
          if (neuron_id < 4'd3) begin
            neuron_id <= neuron_id + 1;
            rom_addr  <= 9'd320 + ({5'd0, neuron_id} + 1) * 16;
            state     <= S_OUTPUT;
          end else begin
            state <= S_ARGMAX;
          end
        end

        S_ARGMAX: begin
          begin
            reg [1:0] best;
            best = 2'd0;
            if (logit[1] > logit[best]) best = 2'd1;
            if (logit[2] > logit[best]) best = 2'd2;
            if (logit[3] > logit[best]) best = 2'd3;
            m_axis_tdata <= best;
          end
          m_axis_tvalid <= 1'b1;
          state <= S_DONE;
        end

        S_DONE: begin
          if (m_axis_tvalid && m_axis_tready) begin
            m_axis_tvalid <= 1'b0;
            state <= S_IDLE;
          end
        end

        default: state <= S_IDLE;
      endcase
    end
  end

  assign s_axis_tready = (state == S_IDLE);

endmodule
