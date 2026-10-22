#==============================================================================
# i2c_master_driver.py
# UVM Master Driver driving the I2C Master Host Interface
#==============================================================================

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from pyuvm import uvm_driver
from i2c_seq_item import I2CSeqItem, RStartType, StretchTarget

class I2CMasterDriver(uvm_driver):
    def __init__(self, name="i2c_master_driver", parent=None):
        super().__init__(name, parent)
        self.dut = None

    def build_phase(self):
        super().build_phase()
        self.dut = cocotb.top

    async def run_phase(self):
        # Default idle values
        self.dut.mst_start.value = 0
        self.dut.mst_reset.value = 0
        self.dut.mst_addr.value = 0
        self.dut.mst_rw.value = 0
        self.dut.mst_data_tx.value = 0
        self.dut.mst_num_bytes.value = 0
        self.dut.tb_sda_force_low.value = 0
        self.dut.tb_scl_force_low.value = 0

        while True:
            item = await self.seq_item_port.get_next_item()
            await self.drive_item(item)
            self.seq_item_port.item_done()

    async def drive_item(self, item: I2CSeqItem):
        # Fault injection: 35ms timeout
        if item.inject_timeout:
            await self.drive_timeout_injection(item)
            return

        # Fault injection: arbitration loss
        if item.inject_arb_loss:
            await self.drive_arb_loss_injection(item)
            return

        # Setup SMBALERT before ARA read transaction
        if item.is_ara or item.alert_pending:
            self.dut.slv_tx_data.value = 0x50
            self.dut.slv_tx_valid.value = 1
            await ClockCycles(self.dut.clk, 5)
            if int(self.dut.slv_alert_pending.value) == 1 or int(self.dut.u_i2c_slave.smbalert_asserted.value) == 1:
                item.alert_pending = True

        # Execute primary transaction
        await self.execute_transaction(item, item.addr, item.rw, item.data_tx, item.burst_len)

        # Handle Repeated START if configured
        if item.rstart_type != RStartType.NO_RSTART:
            item.in_rstart_phase = True
            await ClockCycles(self.dut.clk, 5)
            await self.execute_transaction(
                item, item.rstart_addr, item.rstart_rw, item.rstart_data_tx, item.rstart_burst_len, is_rstart=True
            )
            item.in_rstart_phase = False

    async def execute_transaction(self, item, addr, rw, data_tx, burst_len, is_rstart=False):
        if not is_rstart:
            item.slv_rx_data = []
            item.data_rx = []
        else:
            item.rstart_slv_rx_data = []
            item.rstart_data_rx = []

        # Setup master inputs
        self.dut.mst_addr.value = addr
        self.dut.mst_rw.value = rw
        self.dut.mst_num_bytes.value = burst_len
        self.dut.mst_data_tx.value = data_tx[0] if (data_tx and len(data_tx) > 0) else 0

        # Start pulse held until mst_busy goes high
        self.dut.mst_start.value = 1
        while int(self.dut.mst_busy.value) == 0:
            await RisingEdge(self.dut.clk)
        self.dut.mst_start.value = 0

        # Inject PEC corruption if requested
        if item.corrupt_pec:
            async def corrupt_pec_coro():
                while not (int(self.dut.u_i2c_master.state.value) == 2 and
                           int(self.dut.u_i2c_master.addr_phase.value) == 0 and
                           int(self.dut.u_i2c_master.byte_cnt.value) > burst_len):
                    if int(self.dut.mst_busy.value) == 0:
                        return
                    await RisingEdge(self.dut.clk)
                self.dut.u_i2c_master.shift_reg.value = int(self.dut.u_i2c_master.shift_reg.value) ^ 0xFF
            cocotb.start_soon(corrupt_pec_coro())

        # Handle data capture & staging for write transactions
        if rw == 0:
            if burst_len > 1:
                # Wait until address phase finishes (addr_phase drops to 0)
                while int(self.dut.u_i2c_master.addr_phase.value) == 1:
                    if int(self.dut.mst_busy.value) == 0:
                        break
                    await RisingEdge(self.dut.clk)

                if len(data_tx) > 1:
                    self.dut.mst_data_tx.value = data_tx[1]

                for b in range(burst_len):
                    # Wait for slave rx_valid to go high
                    while int(self.dut.slv_rx_valid.value) == 0:
                        if int(self.dut.mst_busy.value) == 0:
                            break
                        await RisingEdge(self.dut.clk)
                    if int(self.dut.mst_busy.value) == 0:
                        break

                    val = int(self.dut.slv_rx_data.value)
                    if not is_rstart:
                        item.slv_rx_data.append(val)
                    else:
                        item.rstart_slv_rx_data.append(val)

                    if b + 2 < burst_len and b + 2 < len(data_tx):
                        self.dut.mst_data_tx.value = data_tx[b + 2]

                    await RisingEdge(self.dut.clk)
                    while int(self.dut.slv_rx_valid.value) == 1:
                        await RisingEdge(self.dut.clk)
            else:
                while int(self.dut.slv_rx_valid.value) == 0:
                    if int(self.dut.mst_busy.value) == 0:
                        break
                    await RisingEdge(self.dut.clk)
                if int(self.dut.slv_rx_valid.value) == 1:
                    val = int(self.dut.slv_rx_data.value)
                    if not is_rstart:
                        item.slv_rx_data.append(val)
                    else:
                        item.rstart_slv_rx_data.append(val)

        # Handle data capture for read transactions
        elif rw == 1:
            for b in range(burst_len):
                # Wait for MST_SEND_ACK state (state == 7)
                while not (int(self.dut.u_i2c_master.state.value) == 7):
                    if int(self.dut.mst_busy.value) == 0:
                        break
                    await RisingEdge(self.dut.clk)
                if int(self.dut.mst_busy.value) == 0:
                    break
                
                # Wait until state transitions away from MST_SEND_ACK
                while int(self.dut.u_i2c_master.state.value) == 7:
                    await RisingEdge(self.dut.clk)

                rx_val = int(self.dut.mst_data_rx.value)
                if not is_rstart:
                    item.data_rx.append(rx_val)
                else:
                    item.rstart_data_rx.append(rx_val)

        # Wait for transaction to complete
        timeout_cnt = 200000
        while int(self.dut.mst_busy.value) == 1 and timeout_cnt > 0:
            await RisingEdge(self.dut.clk)
            timeout_cnt -= 1

        await ClockCycles(self.dut.clk, 5)

        # Record output status
        if not is_rstart:
            item.ack_error = (int(self.dut.mst_ack_error.value) == 1)
            item.arb_lost = (int(self.dut.mst_arb_lost.value) == 1)
            item.smbus_timeout = (int(self.dut.mst_smbus_timeout.value) == 1)
            item.pec_error = (int(self.dut.mst_pec_error.value) == 1)
            item.slv_pec_error = (int(self.dut.slv_pec_error.value) == 1)
            if not item.is_ara and not getattr(item, 'alert_pending', False):
                item.alert_pending = (int(self.dut.slv_alert_pending.value) == 1)

    async def drive_arb_loss_injection(self, item):
        self.dut.mst_addr.value = item.addr
        self.dut.mst_rw.value = item.rw
        self.dut.mst_num_bytes.value = 1
        self.dut.mst_data_tx.value = 0x00
        self.dut.mst_start.value = 1
        while int(self.dut.mst_busy.value) == 0:
            await RisingEdge(self.dut.clk)
        self.dut.mst_start.value = 0

        while not (int(self.dut.u_i2c_master.state.value) == 2 and
                   int(self.dut.u_i2c_master.sda_oe.value) == 1 and
                   int(self.dut.u_i2c_master.sda_o.value) == 1):
            if int(self.dut.mst_busy.value) == 0:
                break
            await RisingEdge(self.dut.clk)

        self.dut.tb_sda_force_low.value = 1
        await ClockCycles(self.dut.clk, 600)
        item.arb_lost = (int(self.dut.mst_arb_lost.value) == 1)
        self.dut.tb_sda_force_low.value = 0

        while int(self.dut.mst_busy.value) == 1:
            await RisingEdge(self.dut.clk)
        await ClockCycles(self.dut.clk, 5)

    async def drive_timeout_injection(self, item):
        self.dut.mst_addr.value = item.addr
        self.dut.mst_rw.value = 0
        self.dut.mst_num_bytes.value = 1
        self.dut.mst_data_tx.value = 0xAA
        self.dut.mst_start.value = 1
        while int(self.dut.mst_busy.value) == 0:
            await RisingEdge(self.dut.clk)
        self.dut.mst_start.value = 0

        # Simulate SCL low bus hang and advance counter near 35ms threshold
        self.dut.tb_scl_force_low.value = 1
        self.dut.u_i2c_master.smbus_to_cnt.value = 1749990
        await ClockCycles(self.dut.clk, 25)
        item.smbus_timeout = (int(self.dut.mst_smbus_timeout.value) == 1)
        self.dut.tb_scl_force_low.value = 0
        self.dut.mst_reset.value = 1
        await ClockCycles(self.dut.clk, 10)
        self.dut.mst_reset.value = 0
        await ClockCycles(self.dut.clk, 10)

        # Bus recovery: generate STOP condition on bus so slave returns to S_IDLE
        self.dut.tb_sda_force_low.value = 1
        await ClockCycles(self.dut.clk, 20)
        self.dut.tb_sda_force_low.value = 0
        await ClockCycles(self.dut.clk, 20)
