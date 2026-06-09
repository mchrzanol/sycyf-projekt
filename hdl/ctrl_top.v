module ctrl_top (
    input  wire        aclk,
    input  wire        aresetn,
    input  wire        frame_valid,
    output reg         frame_ready,
    output reg         l1_start,
    input  wire        l1_done,
    output reg         l2_start,
    input  wire        l2_done,
    output reg         l3_start,
    input  wire        l3_done,
    output reg [2:0]   frame_count,
    output reg         cmd_ready
);

  localparam [4:0] S_IDLE    = 5'b00001,
                   S_CAPTURE = 5'b00010,
                   S_FEATURE = 5'b00100,
                   S_CLASSIFY= 5'b01000,
                   S_VOTE    = 5'b10000;

  reg [4:0] state;

  always @(posedge aclk) begin
    if (!aresetn) begin
      state       <= S_IDLE;
      frame_ready <= 1'b0;
      l1_start    <= 1'b0;
      l2_start    <= 1'b0;
      l3_start    <= 1'b0;
      frame_count <= 3'd0;
      cmd_ready   <= 1'b0;
    end else begin
      l1_start  <= 1'b0;
      l2_start  <= 1'b0;
      l3_start  <= 1'b0;
      cmd_ready <= 1'b0;

      case (state)
        S_IDLE: begin
          frame_ready <= 1'b1;
          frame_count <= 3'd0;
          if (frame_valid) begin
            state       <= S_CAPTURE;
            frame_ready <= 1'b0;
          end
        end

        S_CAPTURE: begin
          l1_start <= 1'b1;
          state    <= S_FEATURE;
        end

        S_FEATURE: begin
          if (l1_done) begin
            l2_start <= 1'b1;
            state    <= S_CLASSIFY;
          end
        end

        S_CLASSIFY: begin
          if (l2_done) begin
            l3_start    <= 1'b1;
            frame_count <= frame_count + 1;
            state       <= S_VOTE;
          end
        end

        S_VOTE: begin
          if (l3_done) begin
            if (frame_count < 3'd6) begin
              frame_ready <= 1'b1;
              if (frame_valid) begin
                state       <= S_CAPTURE;
                frame_ready <= 1'b0;
              end else begin
                state <= S_IDLE;
              end
            end else begin
              cmd_ready <= 1'b1;
              state     <= S_IDLE;
            end
          end
        end

        default: state <= S_IDLE;
      endcase
    end
  end

endmodule
