#==============================================================================
# Makefile for I2C / SMBus 3.0 UVM Verification (pyuvm + cocotb)
#==============================================================================

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VENV_DIR ?= /home/user/venv_uvm
export PATH := $(VENV_DIR)/bin:$(PATH)

PWD_DIR := $(shell pwd)
RTL_DIR := $(PWD_DIR)/../rtl

VERILOG_SOURCES += $(RTL_DIR)/i2c_pkg.sv
VERILOG_SOURCES += $(RTL_DIR)/smbus_pec.sv
VERILOG_SOURCES += $(RTL_DIR)/i2c_master.sv
VERILOG_SOURCES += $(RTL_DIR)/i2c_slave.sv
VERILOG_SOURCES += $(RTL_DIR)/i2c_top_uvm.sv

TOPLEVEL := i2c_top_uvm
MODULE   := test_i2c_uvm

# Simulation compile flags
COMPILE_ARGS += -g2012 -I $(RTL_DIR)

# Include standard cocotb rules
include $(shell $(VENV_DIR)/bin/cocotb-config --makefiles)/Makefile.sim
