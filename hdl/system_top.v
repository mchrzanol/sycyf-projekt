module system_top (
    input  wire        aclk,
    input  wire        aresetn,
    input  wire [63:0] s_axis_tdata,
    input  wire        s_axis_tvalid,
    output wire        s_axis_tready,
    output wire [1:0]  cmd_out,
    output wire        cmd_valid
);

  wire [94:0] l1_tdata;
  wire        l1_tvalid;
  wire        l1_tready;

  wire [1:0]  l2_tdata;
  wire        l2_tvalid;
  wire        l2_tready;

  wire [8:0]  rom_addr;
  wire [7:0]  rom_dout;

  feature_extractor l1_inst (
      .aclk           (aclk),
      .aresetn        (aresetn),
      .s_axis_tdata   (s_axis_tdata),
      .s_axis_tvalid  (s_axis_tvalid),
      .s_axis_tready  (s_axis_tready),
      .m_axis_tdata   (l1_tdata),
      .m_axis_tvalid  (l1_tvalid),
      .m_axis_tready  (l1_tready)
  );

  weight_rom rom_inst (
      .aclk (aclk),
      .addr (rom_addr),
      .dout (rom_dout)
  );

  classifier_mlp l2_inst (
      .aclk           (aclk),
      .aresetn        (aresetn),
      .s_axis_tdata   (l1_tdata),
      .s_axis_tvalid  (l1_tvalid),
      .s_axis_tready  (l1_tready),
      .m_axis_tdata   (l2_tdata),
      .m_axis_tvalid  (l2_tvalid),
      .m_axis_tready  (l2_tready),
      .rom_addr       (rom_addr),
      .rom_dout       (rom_dout)
  );

  voter6 voter_inst (
      .aclk           (aclk),
      .aresetn        (aresetn),
      .s_axis_tdata   (l2_tdata),
      .s_axis_tvalid  (l2_tvalid),
      .s_axis_tready  (l2_tready),
      .cmd_out        (cmd_out),
      .cmd_valid      (cmd_valid)
  );

endmodule
