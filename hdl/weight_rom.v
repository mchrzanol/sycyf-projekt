module weight_rom (
    input  wire        aclk,
    input  wire [8:0]  addr,
    output reg  [7:0]  dout
);

  reg [7:0] mem [0:511];

  initial begin
    $readmemh("weights_q44.hex", mem);
  end

  always @(posedge aclk) begin
    dout <= mem[addr];
  end

endmodule
