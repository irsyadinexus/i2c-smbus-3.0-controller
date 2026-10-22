#==============================================================================
# i2c_slave_driver.py
# UVM Reactive Slave Driver handling Slave Host Interface & Clock Stretching
#==============================================================================

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from pyuvm import uvm_component
from i2c_seq_item import I2CSeqItem, StretchTarget

class I2CSlaveDriver(uvm_component):
    def __init__(self, name="i2c_slave_driver", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self.current_item = None

    def build_phase(self):
        super().build_phase()
        self.dut = cocotb.top

    def set_active_item(self, item: I2CSeqItem):
        self.current_item = item

    async def run_phase(self):
        self.dut.slv_tx_data.value = 0
        self.dut.slv_tx_valid.value = 0
        self.dut.slv_rx_ready.value = 1

        cocotb.start_soon(self.handle_slave_rx())
        cocotb.start_soon(self.handle_slave_tx())

    async def handle_slave_rx(self):
        while True:
            await RisingEdge(self.dut.clk)
            item = self.current_item
            if item and item.stretch_target in [StretchTarget.BYTE_0, StretchTarget.ALL_BYTES] and item.stretch_cycles_rx > 0:
                if int(self.dut.slv_rx_valid.value) == 1:
                    self.dut.slv_rx_ready.value = 0
                    await ClockCycles(self.dut.clk, item.stretch_cycles_rx)
                    self.dut.slv_rx_ready.value = 1
            else:
                self.dut.slv_rx_ready.value = 1

    async def handle_slave_tx(self):
        while True:
            # Wait for slave to match address in read mode (state == 2: S_ACK_REF)
            while not (int(self.dut.u_i2c_slave.state.value) == 2 and 
                       int(self.dut.u_i2c_slave.my_addr.value) == 1 and 
                       int(self.dut.u_i2c_slave.dir_rw.value) == 1):
                await RisingEdge(self.dut.clk)

            item = self.current_item
            # Determine data to transmit
            if item:
                if getattr(item, 'in_rstart_phase', False):
                    data_list = item.rstart_data_tx if (item.rstart_data_tx and len(item.rstart_data_tx) > 0) else [0x99]
                elif item.data_tx and len(item.data_tx) > 0:
                    data_list = item.data_tx
                else:
                    data_list = [0x3C]
            else:
                data_list = [0x3C]

            # Stretch on byte 0 if configured
            if item and item.stretch_target in [StretchTarget.BYTE_0, StretchTarget.ALL_BYTES] and item.stretch_cycles_tx > 0:
                self.dut.slv_tx_valid.value = 0
                await ClockCycles(self.dut.clk, item.stretch_cycles_tx)

            self.dut.slv_tx_data.value = data_list[0]
            self.dut.slv_tx_valid.value = 1

            for byte_idx in range(len(data_list)):
                while int(self.dut.slv_tx_ready.value) == 0 and int(self.dut.mst_busy.value) == 1:
                    await RisingEdge(self.dut.clk)
                if int(self.dut.mst_busy.value) == 0:
                    break

                if byte_idx + 1 < len(data_list):
                    should_stretch = False
                    if item:
                        if item.stretch_target == StretchTarget.MIDDLE_BYTE and byte_idx == 0:
                            should_stretch = True
                        elif item.stretch_target == StretchTarget.LAST_BYTE and byte_idx == len(data_list) - 2:
                            should_stretch = True
                        elif item.stretch_target == StretchTarget.ALL_BYTES:
                            should_stretch = True

                    if should_stretch and item.stretch_cycles_tx > 0:
                        self.dut.slv_tx_valid.value = 0
                        await ClockCycles(self.dut.clk, item.stretch_cycles_tx)

                    self.dut.slv_tx_data.value = data_list[byte_idx + 1]
                    self.dut.slv_tx_valid.value = 1

                await RisingEdge(self.dut.clk)
                while int(self.dut.slv_tx_ready.value) == 1 and int(self.dut.mst_busy.value) == 1:
                    await RisingEdge(self.dut.clk)

            # Wait until state leaves S_TX_DATA or master finishes
            while int(self.dut.mst_busy.value) == 1 and int(self.dut.u_i2c_slave.state.value) == 3:
                await RisingEdge(self.dut.clk)
            self.dut.slv_tx_valid.value = 0

            # Wait until state leaves S_ACK_REF so we don't retrigger immediately
            while int(self.dut.u_i2c_slave.state.value) == 2:
                await RisingEdge(self.dut.clk)
