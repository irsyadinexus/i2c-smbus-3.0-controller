#==============================================================================
# i2c_bus_monitor.py
# UVM Passive Bus Monitor snooping SCL, SDA, and SMBALERT# wires
#==============================================================================

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge
from pyuvm import uvm_component, uvm_analysis_port
from i2c_seq_item import I2CSeqItem

class I2CBusMonitor(uvm_component):
    def __init__(self, name="i2c_bus_monitor", parent=None):
        super().__init__(name, parent)
        self.ap = uvm_analysis_port("ap", self)
        self.dut = None

    def build_phase(self):
        super().build_phase()
        self.dut = cocotb.top

    async def run_phase(self):
        cocotb.start_soon(self.monitor_bus())

    async def monitor_bus(self):
        scl_prev = 1
        sda_prev = 1
        in_frame = False
        bit_idx = 0
        cur_byte = 0
        addr_phase = True
        frame_addr = 0
        frame_rw = 0
        frame_data = []

        while True:
            await RisingEdge(self.dut.clk)
            try:
                scl = int(self.dut.scl_o.value)
                sda = int(self.dut.sda_o.value)
            except ValueError:
                continue

            # Detect START: SDA falls while SCL is high
            if scl == 1 and sda_prev == 1 and sda == 0:
                in_frame = True
                bit_idx = 0
                cur_byte = 0
                addr_phase = True
                frame_data = []

            # Detect STOP: SDA rises while SCL is high
            elif scl == 1 and sda_prev == 0 and sda == 1 and in_frame:
                in_frame = False
                item = I2CSeqItem("monitored_bus_item")
                item.addr = frame_addr
                item.rw = frame_rw
                item.data_tx = frame_data
                item.burst_len = len(frame_data)
                self.ap.write(item)

            # Sample on SCL rising edge during frame
            elif scl_prev == 0 and scl == 1 and in_frame:
                if bit_idx < 8:
                    cur_byte = (cur_byte << 1) | sda
                    bit_idx += 1
                elif bit_idx == 8: # 9th SCL pulse = ACK/NACK
                    if addr_phase:
                        frame_addr = cur_byte >> 1
                        frame_rw = cur_byte & 0x01
                        addr_phase = False
                    else:
                        frame_data.append(cur_byte)
                    cur_byte = 0
                    bit_idx = 0

            scl_prev = scl
            sda_prev = sda
