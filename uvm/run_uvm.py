#!/usr/bin/env python3
#==============================================================================
# run_uvm.py
# Standalone execution runner for I2C / SMBus 3.0 UVM Testbench
#==============================================================================

import os
import sys
from pathlib import Path
from cocotb_tools.runner import get_runner

def run_uvm_suite():
    proj_dir = Path(__file__).resolve().parent
    rtl_dir = proj_dir.parent / "rtl"

    sources = [
        rtl_dir / "i2c_pkg.sv",
        rtl_dir / "smbus_pec.sv",
        rtl_dir / "i2c_master.sv",
        rtl_dir / "i2c_slave.sv",
        rtl_dir / "i2c_top_uvm.sv",
    ]

    sim = os.getenv("SIM", "icarus")
    runner = get_runner(sim)

    build_args = ["-g2012", f"-I{rtl_dir}"]

    print("=" * 70)
    print(f"Building I2C / SMBus 3.0 UVM RTL with {sim.upper()}...")
    print("=" * 70)

    runner.build(
        sources=sources,
        hdl_toplevel="i2c_top_uvm",
        build_args=build_args,
        always=True,
    )

    print("\n" + "=" * 70)
    print("Launching UVM Simulation Suite (IEEE 1800.2 via pyuvm)...")
    print("=" * 70)

    runner.test(
        hdl_toplevel="i2c_top_uvm",
        test_module="test_i2c_uvm",
        test_dir=str(proj_dir),
    )

if __name__ == "__main__":
    run_uvm_suite()
