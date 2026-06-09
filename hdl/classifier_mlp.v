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

  localparam S_IDLE   = 4'd0,
             S_PRIME  = 4'd1,
             S_HIDDEN = 4'd2,
             S_BIASH  = 4'd3,
             S_BIASH2 = 4'd4,
             S_OPRIME = 4'd5,
             S_OUTPUT = 4'd6,
             S_BIASO  = 4'd7,
             S_BIASO2 = 4'd8,
             S_ARGMAX = 4'd9,
             S_DONE   = 4'd10;

  reg [3:0] state;
  reg [4:0] mac_cnt;
  reg [3:0] neuron_id;

  reg signed [7:0] feature [0:18];
  reg signed [15:0] acc;
  reg signed [7:0] hidden_out [0:15];
  reg signed [15:0] logit [0:3];

  reg signed [15:0] acc_biased;
  reg [1:0] best;
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
            rom_addr  <= 9'd0;
            mac_cnt   <= 5'd0;
            neuron_id <= 4'd0;
            acc       <= 16'sd0;
            state     <= S_PRIME;
          end
        end

        // ROM needs 1 cycle: addr set in IDLE, data available now
        // Advance addr so next data is ready next cycle
        S_PRIME: begin
          rom_addr <= rom_addr + 1;
          mac_cnt  <= 5'd1;
          acc      <= $signed(feature[0]) * $signed(rom_dout);
          state    <= S_HIDDEN;
        end

        S_HIDDEN: begin
          if (mac_cnt < 5'd19) begin
            acc      <= acc + $signed(feature[mac_cnt]) * $signed(rom_dout);
            mac_cnt  <= mac_cnt + 1;
            rom_addr <= rom_addr + 1;
          end else begin
            // All 19 weights consumed. Set addr for bias.
            rom_addr <= 9'd304 + {5'd0, neuron_id};
            state    <= S_BIASH;
          end
        end

        // Wait 1 cycle for bias ROM data
        S_BIASH: begin
          state <= S_BIASH2;
        end

        S_BIASH2: begin
          acc_biased = acc + {{8{rom_dout[7]}}, rom_dout};
          hidden_out[neuron_id] <= (acc_biased[15] == 1'b0)
                                 ? acc_biased[11:4]
                                 : 8'sd0;
          acc     <= 16'sd0;
          mac_cnt <= 5'd0;
          if (neuron_id < 4'd15) begin
            neuron_id <= neuron_id + 1;
            rom_addr  <= ({5'd0, neuron_id} + 1) * 19;
            state     <= S_PRIME;
          end else begin
            neuron_id <= 4'd0;
            rom_addr  <= 9'd320;
            state     <= S_OPRIME;
          end
        end

        // Same as PRIME but for output layer using hidden_out
        S_OPRIME: begin
          rom_addr <= rom_addr + 1;
          mac_cnt  <= 5'd1;
          acc      <= $signed(hidden_out[0]) * $signed(rom_dout);
          state    <= S_OUTPUT;
        end

        S_OUTPUT: begin
          if (mac_cnt < 5'd16) begin
            acc      <= acc + $signed(hidden_out[mac_cnt]) * $signed(rom_dout);
            mac_cnt  <= mac_cnt + 1;
            rom_addr <= rom_addr + 1;
          end else begin
            rom_addr <= 9'd384 + {5'd0, neuron_id};
            state    <= S_BIASO;
          end
        end

        // Wait 1 cycle for bias ROM data
        S_BIASO: begin
          state <= S_BIASO2;
        end

        S_BIASO2: begin
          logit[neuron_id] <= acc + {{8{rom_dout[7]}}, rom_dout};
          acc     <= 16'sd0;
          mac_cnt <= 5'd0;
          if (neuron_id < 4'd3) begin
            neuron_id <= neuron_id + 1;
            rom_addr  <= 9'd320 + ({5'd0, neuron_id} + 1) * 16;
            state     <= S_OPRIME;
          end else begin
            state <= S_ARGMAX;
          end
        end

        S_ARGMAX: begin
          best = 2'd0;
          if (logit[1] > logit[best]) best = 2'd1;
          if (logit[2] > logit[best]) best = 2'd2;
          if (logit[3] > logit[best]) best = 2'd3;
          m_axis_tdata  <= best;
          m_axis_tvalid <= 1'b1;
          state         <= S_DONE;
        end

        S_DONE: begin
          if (m_axis_tvalid && m_axis_tready) begin
            m_axis_tvalid <= 1'b0;
            state         <= S_IDLE;
          end
        end

        default: state <= S_IDLE;
      endcase
    end
  end

  assign s_axis_tready = (state == S_IDLE);

endmodule
