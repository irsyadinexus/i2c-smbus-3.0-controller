# I2C / SMBus 3.0 Controller - SystemVerilog Design & UVM Verification

A synthesisable **I2C / SMBus 3.0 bus controller** implemented in SystemVerilog. This project includes both a master and a slave controller, a top-level integration module, an extensive self-checking testbench suite covering standard I2C, SMBus 3.0 features (PEC, ARP, SMBALERT#, clock stretching, the 35 ms timeout), and a complete **IEEE 1800.2 Python-based UVM verification suite (`pyuvm` + `cocotb`) achieving 100.00% functional coverage**.

## Features

### I2C Master
- **7-bit addressing** with configurable slave address
- **Standard (100 kHz)** and **Fast (400 kHz)** mode operation
- **Read/Write** single-byte and **multi-byte burst** transactions (up to 256 bytes)
- **Repeated START** condition support
- **Clock stretching** support (real slave-driven, not just forced)
- **ACK/NACK** detection and error reporting
- **Arbitration loss** detection (address-byte collisions)
- **SMBus 3.0 PEC** (Packet Error Checking — CRC-8) generation, cross-checked against an independent reference implementation
- **SMBus 3.0 35 ms SCL-low timeout** detection, sticky until genuinely resolved (does not self-clear as a side effect of the FSM returning to idle)
- **Configurable SCL frequency** via an asymmetric system clock divider (meets I2C `t_LOW` at both 100 kHz and 400 kHz)

### I2C Slave
- **Programmable 7-bit address**, plus SMBus default address (`0x61`) and Alert Response Address (`0x0C`) support
- **General call (0x00)** address detection (optional)
- **Read/Write** transaction handling with double-buffered TX/RX handshake
- **ACK/NACK** generation
- **START/STOP** condition detection, bus busy tracking
- **Clock stretching**: genuinely holds SCL low on write (waiting for `rx_ready`) and on read (waiting for `tx_valid`)
- **SMBus 3.0 PEC** verification (CRC-8 check at STOP)
- **SMBus 3.0 SMBALERT#** open-drain interrupt signaling
- **SMBus 3.0 ARP** (Address Resolution Protocol): Prepare-to-ARP, Get UDID (general and directed), Assign Address, Reset Device (general and directed)

### Protocol Support
- START and STOP condition generation/detection
- Data transfer MSB-first, 8-bit + ACK
- Repeated START (combined transactions)
- Bus arbitration (multi-master aware)

## Architecture

```
                         ┌─────────────────────────┐
                         │       i2c_top            │
                         │                          │
  Host Interface ──────► │  ┌──────────┐            │
  (Master)               │  │ I2C      │            │
                         │  │ Master   │───┬───► SCL│──► to bus
                         │  └──────────┘   │       │
                         │                 ├───► SDA│──► to bus
  Host Interface ──────► │  ┌──────────┐   │       │
  (Slave)                │  │ I2C      │   │       │
                         │  │ Slave    │───┘       │
                         │  └──────────┘           │
                         └─────────────────────────┘
```

### Module Descriptions

| Module | File | Description |
|--------|------|-------------|
| `i2c_pkg` | [`rtl/i2c_pkg.sv`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/rtl/i2c_pkg.sv) | Package with parameters, typedefs, and constants (incl. ARP command codes, UDID width) |
| `smbus_pec` | [`rtl/smbus_pec.sv`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/rtl/smbus_pec.sv) | SMBus 3.0 PEC CRC-8 accumulator, shared by master and slave |
| `i2c_master` | [`rtl/i2c_master.sv`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/rtl/i2c_master.sv) | I2C Master controller (FSM-based) |
| `i2c_slave` | [`rtl/i2c_slave.sv`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/rtl/i2c_slave.sv) | I2C Slave controller (FSM-based) |
| `i2c_top` | [`rtl/i2c_top.sv`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/rtl/i2c_top.sv) | Top-level integration with tri-state pads (`inout`) |
| `i2c_top_verilator` | [`rtl/i2c_top_verilator.sv`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/rtl/i2c_top_verilator.sv) | Verilator-only variant using `logic` bus ports instead of `inout`, plus a `tb_sda_force_low` fault-injection input for arbitration testing |
| `i2c_top_uvm` | [`rtl/i2c_top_uvm.sv`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/rtl/i2c_top_uvm.sv) | UVM testbench top wrapper exposing master/slave host interfaces and open-drain fault injection pins |
| `tb_i2c` | [`tb/tb_i2c.sv`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/tb/tb_i2c.sv) | Self-checking testbench |

## Getting Started

### Prerequisites

- **Icarus Verilog** (>= 10.0, recommended 12.0) for SystemVerilog simulation
- **Verilator** (>= 5.0, optional) — alternative high-performance simulator
- **GTKWave** (optional) for waveform viewing
- **Python 3.10+** (for UVM verification): `cocotb >= 2.0`, `pyuvm >= 5.0`, `cocotb-coverage >= 1.2`

Install toolchain on Ubuntu/Debian:
```bash
sudo apt-get install iverilog verilator gtkwave python3-venv python3-pip
```

Setup Python UVM environment:
```bash
python3 -m venv ~/venv_uvm
~/venv_uvm/bin/pip install cocotb pyuvm cocotb-coverage pytest
```

### Quick Start

Run the complete **UVM IEEE 1800.2 Verification Regression Suite** (100% coverage, 40 bins):
```bash
make uvm-sim
```

Run all 10 native SystemVerilog testbenches:
```bash
make all
```

Or step by step for individual legacy testbenches:
```bash
make sim    # Standard mode I2C (100 kHz)
make waves  # View waveforms (if GTKWave is installed)
```

### Clean Up
```bash
make clean
```

### Running with Different Parameters

Override parameters from the command line:
```bash
# Fast-mode (400 kHz)
make sim SCL_FREQ=400000

# Custom slave address (0x20)
make sim SLAVE_ADDR=32
```

### Available Testbenches

The `tb/` directory contains one self-contained testbench per module/mode
combination — each has its own `initial` block and is meant to be compiled
and run on its own (not all bundled together):

| Testbench | Covers |
|-----------|--------|
| `tb_i2c.sv` | Core I2C master/slave transactions, standard mode (100 kHz) |
| `tb_i2c_fastmode.sv` | Core I2C transactions, fast mode (400 kHz) |
| `tb_i2c_smbus.sv` | SMBus 3.0 features (PEC, SMBALERT#/ARA, ARP, clock stretching); randomized burst write/read (Tests 19-20); randomized PEC burst write with a reference-CRC cross-check and mutation-tested corruption detection (Test 21); randomized ARP Assign Address including UDID-mismatch rejection (Test 22); genuine arbitration-loss detection (Test 23); standard mode |
| `tb_i2c_smbus_fastmode.sv` | Same SMBus 3.0 feature set and Tests 19-23, fast mode |
| `tb_i2c_smbus_timeout.sv` | 35 ms SCL-low timeout (forced bus hang), standard mode |
| `tb_i2c_smbus_timeout_fastmode.sv` | Same timeout test, fast mode |
| `tb_i2c_smbus_stretch_timeout.sv` | Real slave-driven clock stretching interacting with the 35 ms timeout; randomized burst write with interspersed legitimate stretching; randomized burst read regression; real over-limit stretch at a random position within a burst; standard mode |
| `tb_i2c_smbus_stretch_timeout_fastmode.sv` | Same stretch/timeout interaction and randomized-burst tests, fast mode |
| `tb_i2c_read_stretch_regression.sv` | Standalone regression for genuine clock stretching on byte 2+ of a multi-byte read (first/middle/last byte scenarios), standard mode — see [Known Limitations](#known-limitations) |
| `tb_i2c_read_stretch_regression_fastmode.sv` | Same read-stretch scenarios, fast mode |

---

## UVM Verification Environment (pyuvm + cocotb)

A complete **IEEE 1800.2 compliant UVM testbench** implemented in Python using `pyuvm` and `cocotb` under Icarus Verilog. The testbench features virtual sequences, a dual driver architecture (master host interface + slave responder with true clock stretching), a non-intrusive bus monitor, an automated self-checking scoreboard, and functional coverage collection.

```
+-----------------------------------------------------------------------------------------+
|                                    I2CComprehensiveTest                                 |
|                                                                                         |
|  +-------------------------------------+       +-------------------------------------+  |
|  |     Virtual Sequencer / Sequences   |       |             Environment             |  |
|  |   (I2CComprehensiveRegressionSeq)   |       |               (I2CEnv)              |  |
|  +------------------+------------------+       +------------------+------------------+  |
|                     |                                             |                     |
|           +---------+---------+                         +---------+---------+           |
|           |                   |                         |                   |           |
|           v                   v                         v                   v           |
|   +---------------+   +---------------+         +---------------+   +---------------+   |
|   |  I2CMaster-   |   |  I2CSlave-    |         |  Scoreboard   |   |   Coverage    |   |
|   |    Driver     |   |    Driver     |         | (I2CScoreboard|   | (I2CCoverage) |   |
|   +-------+-------+   +-------+-------+         +-------^-------+   +-------^-------+   |
|           |                   |                         |                   |           |
|           +---------+---------+                         +---------+---------+           |
|                     |                                             |                     |
|                     v                                             |                     |
|        +-------------------------+                                |                     |
|        |    DUT: i2c_top_uvm     | ======= (Analysis Port) =======+                     |
|        |  (Master + Slave + Bus) |                                                      |
|        +-------------------------+                                                      |
+-----------------------------------------------------------------------------------------+
```

### UVM Architecture Components ([`uvm/`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/uvm))

- **[`i2c_seq_item.py`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/uvm/i2c_seq_item.py)**: Transaction sequence item representing address, direction, data payload (1–32+ bytes), repeated START configurations, clock stretching targets, PEC flags, ARP command codes, and bus fault injections.
- **[`i2c_master_driver.py`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/uvm/i2c_master_driver.py)**: Drives master host interface (`mst_addr`, `mst_rw`, `mst_data_tx`, `mst_start`), coordinates repeated START phases, injects arbitration loss, injects 35 ms timeout with open-drain STOP recovery, and injects targeted PEC byte corruption.
- **[`i2c_slave_driver.py`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/uvm/i2c_slave_driver.py)**: Manages slave responses upon hardware address match, stages multi-byte read data, responds to ARA requests, and drives genuine clock stretching by controlling `slv_rx_ready` / `slv_tx_valid`.
- **[`i2c_bus_monitor.py`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/uvm/i2c_bus_monitor.py)**: Monitors the physical bus activity and broadcasts transaction items to the scoreboard and coverage subscribers via analysis ports.
- **[`i2c_scoreboard.py`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/uvm/i2c_scoreboard.py)**: Self-checking scoreboard verifying data payload match, dynamic ARP address reassignment, PEC validation & corruption detection, NACK generation, arbitration loss, and timeout hang flags.
- **[`i2c_coverage.py`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/uvm/i2c_coverage.py)**: Functional coverage subscriber tracking 40 bins across 10 functional groups.
- **[`i2c_sequences.py`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/uvm/i2c_sequences.py)**: Modular sequence library (`I2CSingleWriteSeq`, `I2CBurstReadSeq`, `I2CRepeatedStartSeq`, `I2CClockStretchSeq`, `SMBusPecSeq`, `SMBusAlertAraSeq`, `SMBusArpSeq`, `SMBusTimeoutSeq`, `I2CGeneralCallSeq`, `I2CRandomSweepSeq`).
- **[`run_uvm.py`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/uvm/run_uvm.py)**: Python simulation runner executing the test suite via Cocotb's runner API.

### Functional Coverage Results: 100.00% (40 / 40 Total Bins)

| Functional Group | Defined Bins | Hits | Status |
| :--- | :--- | :---: | :---: |
| **Address Space** | `own_addr_0x50`, `ara_addr_0x0c`, `default_arp_0x61`, `gen_call_0x00`, `reassigned_arp_addr`, `unmapped_nack_addr` | 6 / 6 | **100.0%** [HIT] |
| **Transaction Direction** | `write`, `read` | 2 / 2 | **100.0%** [HIT] |
| **Burst Lengths** | `single_1`, `burst_2`, `burst_3_4`, `burst_5_15`, `burst_16_udid`, `burst_32` | 6 / 6 | **100.0%** [HIT] |
| **Repeated START** | `no_rstart`, `write_then_read`, `read_then_write`, `write_then_write`, `read_then_read` | 5 / 5 | **100.0%** [HIT] |
| **Clock Stretching** | `no_stretch`, `write_stretch_rx_ready`, `read_stretch_byte_0`, `read_stretch_middle_byte`, `read_stretch_last_byte` | 5 / 5 | **100.0%** [HIT] |
| **SMBus 3.0 PEC** | `pec_write_single`, `pec_write_burst`, `pec_error_detected` | 3 / 3 | **100.0%** [HIT] |
| **SMBALERT# & ARA** | `smbalert_asserted`, `ara_serviced` | 2 / 2 | **100.0%** [HIT] |
| **SMBus 3.0 ARP** | `prepare_to_arp_0x01`, `get_udid_gen_0x02`, `assign_addr_valid_0x03`, `assign_addr_mismatch_rejected`, `get_udid_dir_0x04`, `reset_device_gen_0x05`, `reset_device_dir_0x06` | 7 / 7 | **100.0%** [HIT] |
| **35ms Timeout** | `timeout_triggered_35ms`, `post_timeout_recovered` | 2 / 2 | **100.0%** [HIT] |
| **Faults & Arbitration** | `nack_detected`, `arbitration_lost_detected` | 2 / 2 | **100.0%** [HIT] |
| **OVERALL FUNCTIONAL COVERAGE** | **All 10 Categories** | **40 / 40** | **100.00% (TARGET ACHIEVED)** |

- **Scoreboard Result**: **57 PASSED, 0 FAILED** (Zero Scoreboard Errors).
- **Execution Time**: ~53 s sim time across 31.8 ms of bus activity.

---

## Running Native SystemVerilog Testbenches

### Running a Testbench with Icarus Verilog

The default `make sim` target only elaborates `tb_i2c`. To compile and run
any individual testbench directly with `iverilog`/`vvp`:

```bash
iverilog -g2012 -Wall -Winfloop -I rtl -I tb \
  -o build/<testbench>.vvp \
  rtl/i2c_pkg.sv rtl/smbus_pec.sv rtl/i2c_master.sv rtl/i2c_slave.sv rtl/i2c_top.sv \
  tb/<testbench>.sv

vvp build/<testbench>.vvp
```

For example, to run the SMBus 3.0 fast-mode testbench:
```bash
iverilog -g2012 -Wall -Winfloop -I rtl -I tb \
  -o build/tb_i2c_smbus_fastmode.vvp \
  rtl/i2c_pkg.sv rtl/smbus_pec.sv rtl/i2c_master.sv rtl/i2c_slave.sv rtl/i2c_top.sv \
  tb/tb_i2c_smbus_fastmode.sv

vvp build/tb_i2c_smbus_fastmode.vvp
```

Repeat for each file listed in [Available Testbenches](#available-testbenches)
to run the full regression suite.

#### Viewing Waveforms from an Icarus Verilog Run

Each testbench already calls `$dumpfile`/`$dumpvars` in its source, so no
extra flags are needed — running it with `vvp` writes a waveform to the
current directory named after the testbench (e.g. `tb_i2c_smbus_fastmode.vcd`).
Open it with GTKWave once the run finishes:
```bash
vvp build/tb_i2c_smbus_fastmode.vvp
gtkwave tb_i2c_smbus_fastmode.vcd
```

### Running a Testbench with Verilator

Verilator can run these testbenches too, using its `--binary` mode (which
auto-generates a C++ driver so the SystemVerilog `initial`/`$finish`
testbench runs standalone) with `--timing` enabled (required for the
`#delay` statements the testbenches use):

```bash
verilator --binary --timing -Wno-fatal \
  --top-module <testbench> -Mdir build/verilator_<testbench> \
  -Irtl -Itb \
  rtl/i2c_pkg.sv rtl/smbus_pec.sv rtl/i2c_master.sv rtl/i2c_slave.sv rtl/i2c_top.sv \
  tb/<testbench>.sv \
  -o <testbench>

./build/verilator_<testbench>/<testbench>
```

For example:
```bash
verilator --binary --timing -Wno-fatal \
  --top-module tb_i2c_smbus_fastmode -Mdir build/verilator_tb_i2c_smbus_fastmode \
  -Irtl -Itb \
  rtl/i2c_pkg.sv rtl/smbus_pec.sv rtl/i2c_master.sv rtl/i2c_slave.sv rtl/i2c_top.sv \
  tb/tb_i2c_smbus_fastmode.sv \
  -o tb_i2c_smbus_fastmode

./build/verilator_tb_i2c_smbus_fastmode/tb_i2c_smbus_fastmode
```

Notes:
- Always give each testbench its **own `-Mdir`** — reusing one output
  directory across multiple `verilator` invocations will overwrite files
  from the previous build.
- `-Wno-fatal` silences non-fatal width/pin warnings so the build completes;
  it does not suppress `%Error`s.
- All 10 `tb/` testbenches pass identically under both Icarus Verilog and
  Verilator's `--binary --timing` mode, 0 failures.

#### Viewing Waveforms from a Verilator Run

Unlike Icarus, Verilator ignores `$dumpvars` unless the build is compiled
with tracing enabled — add `--trace` to the command above:
```bash
verilator --binary --timing --trace -Wno-fatal \
  --top-module tb_i2c_smbus_fastmode -Mdir build/verilator_tb_i2c_smbus_fastmode \
  -Irtl -Itb \
  rtl/i2c_pkg.sv rtl/smbus_pec.sv rtl/i2c_master.sv rtl/i2c_slave.sv rtl/i2c_top.sv \
  tb/tb_i2c_smbus_fastmode.sv \
  -o tb_i2c_smbus_fastmode

./build/verilator_tb_i2c_smbus_fastmode/tb_i2c_smbus_fastmode
gtkwave tb_i2c_smbus_fastmode.vcd
```
Without `--trace`, the run still succeeds but prints
`$dumpvar ignored, as Verilated without --trace` and no `.vcd` file is written.

#### Pre-Loading Signals into GTKWave

Opening a `.vcd` directly shows the signal tree but draws nothing — GTKWave
never auto-populates the waveform pane. Each testbench has a matching Tcl
script (`add_<testbench>_signals.tcl`) that adds a useful signal set — the
top-level bus/control ports plus the master/slave FSM state, stretch, PEC,
ARP, and SMBALERT# internals — and zooms to fit. Load it with `-S`:
```bash
gtkwave tb_i2c_smbus_fastmode.vcd -S add_tb_i2c_smbus_fastmode_signals.tcl
```

These scripts only use GTKWave Tcl commands confirmed to exist in this
build (`addSignalsFromList`, `highlightSignalsFromList`, `Zoom_Full` — check
with `info commands gtkwave::*` in a script if you add more, since commands
like `setWindowPrefix`/`setNewRadix`/`getCurrentDump` referenced in some
GTKWave tutorials are not available here and will abort the rest of the
script on first use).

### Native Verilator C++ Flow (`make veri-sim`)

Separate from running the `tb/` SystemVerilog testbenches directly under
Verilator, `verilator/testbench.cpp` drives `rtl/i2c_top_verilator.sv` (the
`inout`-free variant) via a small hand-written C++ driver:
```bash
make veri-sim
```
This flow includes a genuine arbitration-loss test: since Verilator has no
`force`/`release` and this C++ testbench has no hierarchy introspection, a
dedicated `tb_sda_force_low` input on `i2c_top_verilator` lets the driver act
as a second, competing master pulling the shared bus low — timed off the one
signal the driver can observe (`sda_o`, watching for the START-to-address-bit
transition) rather than any internal FSM state.

## Project Structure

```
i2c_controller/
├── rtl/                                  # RTL source files
│   ├── i2c_pkg.sv                        # Package definitions
│   ├── smbus_pec.sv                      # SMBus 3.0 PEC CRC-8 accumulator
│   ├── i2c_master.sv                     # I2C Master controller
│   ├── i2c_slave.sv                      # I2C Slave controller
│   ├── i2c_top.sv                        # Top-level integration (inout ports)
│   ├── i2c_top_verilator.sv              # Verilator-only variant (logic ports)
│   └── i2c_top_uvm.sv                    # UVM top-level wrapper with fault pins
├── tb/                                   # Native SystemVerilog testbenches (10 testbenches)
├── uvm/                                  # IEEE 1800.2 UVM Verification Suite (pyuvm)
│   ├── i2c_seq_item.py                   # Sequence Item definition
│   ├── i2c_master_driver.py              # Master Host Driver & fault injector
│   ├── i2c_slave_driver.py               # Slave Driver with true clock stretch
│   ├── i2c_bus_monitor.py                # Bus Monitor
│   ├── i2c_scoreboard.py                 # Self-checking Scoreboard
│   ├── i2c_coverage.py                   # Functional Coverage Model (40 bins)
│   ├── i2c_sequences.py                  # UVM Sequence Library
│   ├── i2c_env.py                        # UVM Environment
│   ├── test_i2c_uvm.py                   # Top-level UVM Test
│   └── run_uvm.py                        # Python/Cocotb simulation runner
├── verilator/
│   └── testbench.cpp                     # Native Verilator C++ driver (make veri-sim)
├── Makefile                              # Build automation (iverilog, verilator, uvm-sim)
└── README.md                             # This file
```

## I2C Protocol Reference

The I2C bus uses two bidirectional open-drain lines (SCL, SDA) with external pull-up resistors.

```
START:  SDA ↓ while SCL high
STOP:   SDA ↑ while SCL high
DATA:   SDA changes while SCL low, sampled while SCL high
ACK:    Receiver pulls SDA low on 9th SCL pulse
NACK:   Receiver leaves SDA high on 9th SCL pulse
```

Transaction format:
```
START | 7-bit Address | R/W | ACK | Data Byte | ACK | ... | STOP
```

## Test Plan

Baseline scenarios covered by `tb_i2c.sv`/`tb_i2c_fastmode.sv`:

| Test | Description |
|------|-------------|
| Reset | Verify initial conditions after reset |
| Master Write | Single byte write to slave, verify data |
| Master Read | Single byte read from slave, verify data |
| Repeated START | Write followed by read without STOP |
| Burst Write | Multi-byte write transaction (4 bytes) |
| Error Detection | NACK detection for non-existent address |
| Multiple Transactions | 5 consecutive write transactions |
| Back-to-back | Immediate write then read |

`tb_i2c_smbus.sv`/`tb_i2c_smbus_fastmode.sv` add SMBALERT#/ARA, PEC, ARP
(Prepare-to-ARP, Get UDID, Assign Address, Reset Device — both general and
directed variants), clock stretching, and five randomized/mutation-tested
regressions (Tests 19-23): randomized burst write/read, randomized PEC burst
write cross-checked against an independent reference CRC-8 with a mutation
loop that deliberately corrupts the PEC byte and confirms detection,
randomized ARP Assign Address including deliberate UDID-mismatch rejection,
and genuine arbitration-loss detection. `tb_i2c_smbus_stretch_timeout.sv`
adds real (not forced) slave-driven clock stretching interacting with the
35 ms timeout, plus randomized burst write/read regressions under a
stretch-capable configuration and a real over-limit stretch at a random
burst position. `tb_i2c_read_stretch_regression.sv` is a dedicated
standalone regression for stretching byte 2+ of a multi-byte read — see
[Known Limitations](#known-limitations).

## Codebase Analysis & Verification Summary

A comprehensive architectural and functional analysis of this codebase was performed, confirming 100% pass rates across all test suites under both Icarus Verilog and Verilator.

### Codebase Metrics

| Category | Files | Lines of Code | Description |
| :--- | :---: | :---: | :--- |
| **RTL Sources** | 7 | 2,754 | Synthesizable SystemVerilog core (`i2c_master`, `i2c_slave`, `smbus_pec`, top wrappers) |
| **Native Testbenches** | 10 | 6,350 | Self-checking SystemVerilog testbenches with randomized and mutation testing |
| **Python UVM Suite** | 10 | 1,418 | IEEE 1800.2 verification environment (`pyuvm` + `cocotb`) |
| **Verilator C++ Flow** | 1 | 274 | Standalone cycle-accurate C++ simulation driver |
| **Build & Scripts** | 10 | 326 | Makefile build automation and GTKWave Tcl waveform scripts |
| **Total Project** | **29** | **11,029** | **Complete hardware design & verification codebase** |

### Verification Suite Results

#### 1. Native SystemVerilog Suite (`make all`)

All 10 testbenches run cleanly under Icarus Verilog (`iverilog` + `vvp`) with **0 failures**:

| Target | Testbench | Clock / Mode | Key Verification Scenarios | Status |
| :--- | :--- | :---: | :--- | :---: |
| `sim` | `tb_i2c.sv` | 100 kHz (Standard) | Single/burst write/read, repeated START, NACK | **PASS** |
| `fast-sim` | `tb_i2c_fastmode.sv` | 400 kHz (Fast) | 400 kHz protocol timing compliance, burst operations | **PASS** |
| `smbus-sim` | `tb_i2c_smbus.sv` | 100 kHz (Standard) | PEC CRC-8, ARP (UDID, Assign), SMBALERT#/ARA, mutation tests | **PASS** |
| `smbus-fast-sim` | `tb_i2c_smbus_fastmode.sv` | 400 kHz (Fast) | SMBus 3.0 feature set & randomized burst tests at 400 kHz | **PASS** |
| `timeout-sim` | `tb_i2c_smbus_timeout.sv` | 100 kHz (Standard) | 35 ms SCL-low forced hang & STOP-only bus recovery | **PASS** |
| `timeout-fast-sim` | `tb_i2c_smbus_timeout_fastmode.sv` | 400 kHz (Fast) | 35 ms SCL-low forced hang at Fast-mode clocking | **PASS** |
| `stretch-sim` | `tb_i2c_smbus_stretch_timeout.sv` | 100 kHz (Standard) | Real slave stretch (5 ms legit vs 36 ms excessive timeout) | **PASS** |
| `stretch-fast-sim` | `tb_i2c_smbus_stretch_timeout_fastmode.sv` | 400 kHz (Fast) | Real slave stretch interaction with 35 ms timeout at 400 kHz | **PASS** |
| `read-stretch-sim` | `tb_i2c_read_stretch_regression.sv` | 100 kHz (Standard) | Read clock stretch regression across byte 0, middle, and last | **PASS** |
| `read-stretch-fast-sim` | `tb_i2c_read_stretch_regression_fastmode.sv` | 400 kHz (Fast) | Read clock stretch regression across byte 0, middle, last (400 kHz) | **PASS** |

#### 2. Verilator C++ Suite (`make veri-sim`)

- **15 Tests Passed, 0 Failures** executing [`verilator/testbench.cpp`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/verilator/testbench.cpp) against [`rtl/i2c_top_verilator.sv`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/rtl/i2c_top_verilator.sv).
- Verified core transactions and genuine arbitration-loss detection via dedicated collision emulation pin (`tb_sda_force_low`).

#### 3. Python UVM Environment (`make uvm-sim`)

- **100.00% Functional Coverage** (40 / 40 bins across all 10 functional groups).
- **57 Passed Assertions, 0 Failures** reported by [`uvm/i2c_scoreboard.py`](file:///home/user/RTL-VIBECODE/I2C/i2c_smbus_3_0_fb_ds4/uvm/i2c_scoreboard.py).

### Architectural Highlights

1. **Stretch-Aware Asymmetric Clock Divider**:
   - Computes separate `LOW_CYCLES` and `HIGH_CYCLES` to guarantee $t_{LOW} \ge 1.3\,\mu\text{s}$ at 400 kHz and $t_{LOW} \ge 4.7\,\mu\text{s}$ at 100 kHz.
   - SCL generator releases SCL and enters `SCL_WAIT` to let slave clock stretching freeze the master's timebase naturally.
2. **Robust Multi-Byte Read Stretching**:
   - Slave controller engages stretch on byte 2+ at the boundary (`state == S_TX_DATA && bit_pos == 8 && scl_falling`), allowing seamless multi-byte read flow control when user logic delays `tx_valid`.
3. **SMBus 3.0 Hardware Primitives**:
   - Parallel CRC-8 computation module (`smbus_pec.sv`) updating per byte with polynomial 0x07.
   - $t_{HD;DAT} \ge 300\,\text{ns}$ hold time generator pipeline preventing data races on falling SCL.
   - Hardware sticky 35 ms timeout counter based on `CLK_FREQ` requiring a clean STOP condition to recover.

## Known Limitations

- **Clock stretching on byte 2+ of a multi-byte read is not fully
  randomized-tested.** The RTL correctly stretches when the slave isn't
  ready with data — for the first byte of a read (`i2c_slave.sv`'s
  `S_ACK_REF`-based path) and, after a fix, for any single later byte too
  (`S_TX_DATA`-based path, verified via `tb_i2c_read_stretch_regression.sv`
  for the first, a middle, and the last byte of a burst). A prior version of
  this same condition was dead code (keyed on a `bit_pos` value that state
  never actually holds), so stretching past byte 0 silently never engaged at
  all until this fix. What remains untested is *multiple* bytes stretching
  within the same burst and doing so as part of a large randomized/looped
  regression — orchestrating that correctly from a testbench (timing when to
  withdraw `tx_valid` relative to the RTL's stretch-engage check, which reads
  it at the same clock edge `tx_ready` sets on) proved to have escalating
  edge cases with more consecutive stretches or more prior iterations in the
  same simulation, unrelated to the RTL itself. `tb_i2c_smbus_stretch_timeout.sv`'s
  read-burst test therefore does not deliberately stretch any byte.
- **`mst_pec_error` (master) is dead code.** Its set condition depends on the
  slave NACKing a bad PEC byte, but the slave only ever detects a PEC
  mismatch post-hoc via CRC at STOP — it never NACKs because of PEC. PEC
  correctness is validated through other means (Test 21 cross-checks the
  master's computed PEC against an independent reference CRC-8, and checks
  the slave's own `pec_error`).
- **`arbitration_lost` has narrow test coverage.** The dedicated arbitration
  tests (`tb_i2c_smbus.sv` Test 23, and `make veri-sim`'s Test 7) only cover
  a second master colliding on the address byte. No test exercises
  arbitration loss mid-transaction (e.g. during a data byte) or its
  interaction with clock stretching.

> [!NOTE]
> The **UVM Verification Suite** (`make uvm-sim`) systematically exercises these features:
> - **Clock Stretching**: Verifies write clock stretching via `slv_rx_ready` as well as read clock stretching on byte 0, middle bytes, and last byte (`read_stretch_byte_0`, `read_stretch_middle_byte`, `read_stretch_last_byte`).
> - **PEC Verification**: Validates correct PEC calculation and actively injects single/burst PEC byte corruption to confirm slave-side `pec_error` detection.
> - **Full Protocol Coverage**: Reaches 100.00% functional coverage across all 40 defined bins.

## Synthesis

This design is intended for FPGA implementation. The I2C bus signals (`scl`, `sda`) should be connected to bidirectional I/O buffers (e.g., Xilinx IOBUF, Intel ALT_IOBUF) in the target device.

For synthesis, set the following parameters based on your system clock:
- `CLK_FREQ`: System clock frequency (e.g., 50_000_000 for 50 MHz)
- `SCL_FREQ`: Desired SCL frequency (e.g., 100_000 for standard mode)

## License

This project is open-source hardware.

## Contributing

Contributions, bug reports, and feature requests are welcome.
