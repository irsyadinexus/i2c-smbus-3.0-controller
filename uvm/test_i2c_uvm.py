#==============================================================================
# test_i2c_uvm.py
# Main UVM Test definitions for I2C / SMBus 3.0 Controller
# Target: >95% Functional & Code Coverage
#==============================================================================

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles
from pyuvm import uvm_test, uvm_root

from i2c_env import I2CEnv
from i2c_sequences import I2CComprehensiveRegressionSeq

class I2CComprehensiveTest(uvm_test):
    def __init__(self, name="i2c_comprehensive_test", parent=None):
        super().__init__(name, parent)
        self.env = None

    def build_phase(self):
        super().build_phase()
        self.env = I2CEnv("env", self)

    async def run_phase(self):
        self.raise_objection()
        self.logger.info("Starting I2C Comprehensive Regression Sequence...")
        seq = I2CComprehensiveRegressionSeq("main_regression_seq")
        await seq.start(self.env.sequencer)
        await ClockCycles(cocotb.top.clk, 50)
        self.drop_objection()

    def report_phase(self):
        cov_pct, cov_report = self.env.coverage.get_coverage_summary()
        self.logger.info(cov_report)
        
        pass_cnt = self.env.scoreboard.pass_count
        fail_cnt = self.env.scoreboard.fail_count
        
        self.logger.info(f"FINAL VERIFICATION RESULTS: {pass_cnt} PASSED, {fail_cnt} FAILED")
        self.logger.info(f"FINAL FUNCTIONAL COVERAGE: {cov_pct:.2f}% (Target: >95%)")
        
        assert fail_cnt == 0, f"Scoreboard reported {fail_cnt} failures!"
        assert cov_pct >= 95.0, f"Coverage {cov_pct:.2f}% is below target 95%!"

@cocotb.test()
async def run_i2c_uvm_test(dut):
    """Top-level Cocotb test executing the UVM Comprehensive Test Suite"""
    # 50 MHz clock (20 ns period)
    clock = Clock(dut.clk, 20, unit="ns")
    cocotb.start_soon(clock.start())

    # System reset
    dut.rst_n.value = 0
    dut.mst_start.value = 0
    dut.mst_reset.value = 0
    dut.mst_addr.value = 0
    dut.mst_rw.value = 0
    dut.mst_data_tx.value = 0
    dut.mst_num_bytes.value = 0
    dut.slv_tx_data.value = 0
    dut.slv_tx_valid.value = 0
    dut.slv_rx_ready.value = 1
    dut.tb_sda_force_low.value = 0
    dut.tb_scl_force_low.value = 0

    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    # Launch PyUVM
    await uvm_root().run_test("I2CComprehensiveTest")
