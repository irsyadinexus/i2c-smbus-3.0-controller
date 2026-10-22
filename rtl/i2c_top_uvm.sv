//==============================================================================
// i2c_top_uvm.sv — UVM Verification Top-Level Wrapper
//==============================================================================

`timescale 1ns / 1ps

import i2c_pkg::*;

module i2c_top_uvm #(
  parameter int CLK_FREQ          = 50_000_000,
  parameter int SCL_FREQ          = 100_000,
  parameter int MST_BURST_LEN     = 1,
  parameter bit  SMBUS_ENABLE     = 1'b1,
  parameter bit  SMBUS_PEC_ENABLE = 1'b1,
  parameter logic [6:0] SLV_ADDR  = 7'h50,
  parameter bit         GEN_CALL  = 1'b1,
  parameter bit         SMBALERT_ENABLE = 1'b1,
  parameter bit         SMARP_ENABLE    = 1'b1,
  parameter logic [127:0] UDID    = 128'hA1B2_C0DE_0000_0000_00000000_00000000,
  parameter bit         SLV_STRETCH_ENABLE = 1'b1
) (
  input  logic       clk,
  input  logic       rst_n,

  // Testbench fault injection inputs (open-drain simulation)
  input  logic       tb_sda_force_low,
  input  logic       tb_scl_force_low,

  // Master Host Interface
  input  logic       mst_start,
  input  logic       mst_reset,
  input  logic [6:0] mst_addr,
  input  logic       mst_rw,
  input  logic [7:0] mst_data_tx,
  output logic [7:0] mst_data_rx,
  input  logic [7:0] mst_num_bytes,
  output logic       mst_busy,
  output logic       mst_done,
  output logic       mst_ack_error,
  output logic       mst_arb_lost,
  output logic       mst_smbus_timeout,
  output logic       mst_pec_error,

  // Slave Host Interface
  input  logic [7:0] slv_tx_data,
  input  logic       slv_tx_valid,
  output logic       slv_tx_ready,
  output logic [7:0] slv_rx_data,
  output logic       slv_rx_valid,
  input  logic       slv_rx_ready,
  output logic       slv_addressed,
  output logic       slv_dir_rw,
  output logic       slv_busy,
  output logic       slv_pec_error,
  output logic       slv_alert_pending,

  // I2C Bus outputs
  output logic       scl_o,
  output logic       sda_o,
  output logic       smbalert_n_o
);

  logic scl_o_mst, scl_oe_mst;
  logic sda_o_mst, sda_oe_mst;
  logic scl_i_mst, sda_i_mst;

  logic sda_o_slv, sda_oe_slv;
  logic scl_o_slv, scl_oe_slv;
  logic slv_smbalert_n_o_int, slv_smbalert_n_oe;

  logic scl_driven_low, sda_driven_low;

  always_comb begin
    scl_driven_low = (scl_oe_mst && !scl_o_mst) || (scl_oe_slv && !scl_o_slv) || tb_scl_force_low;
    sda_driven_low = (sda_oe_mst && !sda_o_mst) || (sda_oe_slv && !sda_o_slv) || tb_sda_force_low;
    scl_o = scl_driven_low ? 1'b0 : 1'b1;
    sda_o = sda_driven_low ? 1'b0 : 1'b1;
  end

  assign scl_i_mst = scl_o;
  assign sda_i_mst = sda_o;

  i2c_master #(
    .CLK_FREQ         (CLK_FREQ),
    .SCL_FREQ         (SCL_FREQ),
    .BURST_LENGTH     (MST_BURST_LEN),
    .SMBUS_ENABLE     (SMBUS_ENABLE),
    .SMBUS_PEC_ENABLE (SMBUS_PEC_ENABLE)
  ) u_i2c_master (
    .clk             (clk),
    .rst_n           (rst_n),
    .start           (mst_start),
    .reset           (mst_reset),
    .addr            (mst_addr),
    .rw              (mst_rw),
    .data_tx         (mst_data_tx),
    .data_rx         (mst_data_rx),
    .num_bytes       (mst_num_bytes),
    .busy            (mst_busy),
    .done            (mst_done),
    .ack_error       (mst_ack_error),
    .arbitration_lost(mst_arb_lost),
    .smbus_timeout   (mst_smbus_timeout),
    .pec_error       (mst_pec_error),
    .bus_busy        ('0),
    .scl_o           (scl_o_mst),
    .scl_oe          (scl_oe_mst),
    .scl_i           (scl_i_mst),
    .sda_o           (sda_o_mst),
    .sda_oe          (sda_oe_mst),
    .sda_i           (sda_i_mst)
  );

  i2c_slave #(
    .SLAVE_ADDR       (SLV_ADDR),
    .GEN_CALL         (GEN_CALL),
    .SMBUS_PEC_ENABLE (SMBUS_PEC_ENABLE),
    .SMBALERT_ENABLE  (SMBALERT_ENABLE),
    .SMARP_ENABLE     (SMARP_ENABLE),
    .UDID             (UDID),
    .SLV_STRETCH_ENABLE (SLV_STRETCH_ENABLE)
  ) u_i2c_slave (
    .clk              (clk),
    .rst_n            (rst_n),
    .tx_data          (slv_tx_data),
    .tx_valid         (slv_tx_valid),
    .tx_ready         (slv_tx_ready),
    .rx_data          (slv_rx_data),
    .rx_valid         (slv_rx_valid),
    .rx_ready         (slv_rx_ready),
    .addressed        (slv_addressed),
    .dir_rw           (slv_dir_rw),
    .busy             (slv_busy),
    .gen_call_detected(),
    .start_detected   (),
    .stop_detected    (),
    .pec_error        (slv_pec_error),
    .alert_pending    (slv_alert_pending),
    .scl_i            (scl_o),
    .scl_o_slv        (scl_o_slv),
    .scl_oe_slv       (scl_oe_slv),
    .sda_o            (sda_o_slv),
    .sda_oe           (sda_oe_slv),
    .sda_i            (sda_o),
    .smbalert_n_o     (slv_smbalert_n_o_int),
    .smbalert_n_oe    (slv_smbalert_n_oe)
  );

  assign smbalert_n_o = (slv_smbalert_n_oe && !slv_smbalert_n_o_int) ? 1'b0 : 1'b1;

endmodule : i2c_top_uvm
