#==============================================================================
# i2c_sequences.py
# UVM Sequence Library for I2C / SMBus 3.0 Verification
#==============================================================================

from pyuvm import uvm_sequence
from i2c_seq_item import I2CSeqItem, RStartType, StretchTarget
import random

class I2CBaseSeq(uvm_sequence):
    def __init__(self, name="i2c_base_seq"):
        super().__init__(name)

class I2CSingleWriteSeq(I2CBaseSeq):
    async def body(self):
        item = I2CSeqItem("single_write_item")
        item.addr = 0x50
        item.rw = 0
        item.burst_len = 1
        item.data_tx = [0xAB]
        await self.start_item(item)
        await self.finish_item(item)

class I2CSingleReadSeq(I2CBaseSeq):
    async def body(self):
        item = I2CSeqItem("single_read_item")
        item.addr = 0x50
        item.rw = 1
        item.burst_len = 1
        item.data_tx = [0x3C]
        await self.start_item(item)
        await self.finish_item(item)

class I2CBurstWriteSeq(I2CBaseSeq):
    async def body(self):
        lengths = [2, 4, 8, 16, 32]
        for bl in lengths:
            item = I2CSeqItem(f"burst_write_len_{bl}")
            item.addr = 0x50
            item.rw = 0
            item.burst_len = bl
            item.data_tx = [(0x10 + i) & 0xFF for i in range(bl)]
            if item.data_tx[0] in [0x01, 0x02, 0x03, 0x04, 0x05, 0x06]:
                item.data_tx[0] = 0x50
            await self.start_item(item)
            await self.finish_item(item)

class I2CBurstReadSeq(I2CBaseSeq):
    async def body(self):
        lengths = [2, 4, 8, 16]
        for bl in lengths:
            item = I2CSeqItem(f"burst_read_len_{bl}")
            item.addr = 0x50
            item.rw = 1
            item.burst_len = bl
            item.data_tx = [(0x80 + i) & 0xFF for i in range(bl)]
            await self.start_item(item)
            await self.finish_item(item)

class I2CRepeatedStartSeq(I2CBaseSeq):
    async def body(self):
        combos = [
            (RStartType.WRITE_THEN_READ, 0, 1),
            (RStartType.READ_THEN_WRITE, 1, 0),
            (RStartType.WRITE_THEN_WRITE, 0, 0),
            (RStartType.READ_THEN_READ, 1, 1),
        ]
        for r_type, dir1, dir2 in combos:
            item = I2CSeqItem(f"rstart_{r_type.name}")
            item.addr = 0x50
            item.rw = dir1
            item.burst_len = 1
            item.data_tx = [0x11]
            item.rstart_type = r_type
            item.rstart_addr = 0x50
            item.rstart_rw = dir2
            item.rstart_burst_len = 1
            item.rstart_data_tx = [0x22]
            await self.start_item(item)
            await self.finish_item(item)

class I2CNackSeq(I2CBaseSeq):
    async def body(self):
        item = I2CSeqItem("nack_unmapped_item")
        item.addr = 0x7F
        item.rw = 0
        item.burst_len = 1
        item.data_tx = [0xFF]
        item.inject_nack = True
        await self.start_item(item)
        await self.finish_item(item)

class I2CClockStretchSeq(I2CBaseSeq):
    async def body(self):
        # 1. Write stretch
        wr_item = I2CSeqItem("write_stretch_item")
        wr_item.addr = 0x50
        wr_item.rw = 0
        wr_item.burst_len = 2
        wr_item.data_tx = [0xAA, 0x55]
        wr_item.stretch_target = StretchTarget.BYTE_0
        wr_item.stretch_cycles_rx = 50
        await self.start_item(wr_item)
        await self.finish_item(wr_item)

        # 2. Read stretch byte 0
        rd_item0 = I2CSeqItem("read_stretch_b0_item")
        rd_item0.addr = 0x50
        rd_item0.rw = 1
        rd_item0.burst_len = 2
        rd_item0.data_tx = [0x11, 0x22]
        rd_item0.stretch_target = StretchTarget.BYTE_0
        rd_item0.stretch_cycles_tx = 40
        await self.start_item(rd_item0)
        await self.finish_item(rd_item0)

        # 3. Read stretch middle byte
        rd_item_mid = I2CSeqItem("read_stretch_mid_item")
        rd_item_mid.addr = 0x50
        rd_item_mid.rw = 1
        rd_item_mid.burst_len = 4
        rd_item_mid.data_tx = [0x10, 0x20, 0x30, 0x40]
        rd_item_mid.stretch_target = StretchTarget.MIDDLE_BYTE
        rd_item_mid.stretch_cycles_tx = 40
        await self.start_item(rd_item_mid)
        await self.finish_item(rd_item_mid)

        # 4. Read stretch last byte
        rd_item_last = I2CSeqItem("read_stretch_last_item")
        rd_item_last.addr = 0x50
        rd_item_last.rw = 1
        rd_item_last.burst_len = 3
        rd_item_last.data_tx = [0xA1, 0xB2, 0xC3]
        rd_item_last.stretch_target = StretchTarget.LAST_BYTE
        rd_item_last.stretch_cycles_tx = 40
        await self.start_item(rd_item_last)
        await self.finish_item(rd_item_last)

class SMBusPecSeq(I2CBaseSeq):
    async def body(self):
        # Valid Single PEC
        p1 = I2CSeqItem("pec_single_item")
        p1.addr = 0x50
        p1.rw = 0
        p1.burst_len = 1
        p1.data_tx = [0x77]
        p1.is_pec = True
        await self.start_item(p1)
        await self.finish_item(p1)

        # Valid Burst PEC
        p2 = I2CSeqItem("pec_burst_item")
        p2.addr = 0x50
        p2.rw = 0
        p2.burst_len = 4
        p2.data_tx = [0x12, 0x34, 0x56, 0x78]
        p2.is_pec = True
        await self.start_item(p2)
        await self.finish_item(p2)

        # Corrupted PEC
        p3 = I2CSeqItem("pec_corrupt_item")
        p3.addr = 0x50
        p3.rw = 0
        p3.burst_len = 2
        p3.data_tx = [0xDE, 0xAD]
        p3.is_pec = True
        p3.corrupt_pec = True
        await self.start_item(p3)
        await self.finish_item(p3)

class SMBusAlertAraSeq(I2CBaseSeq):
    async def body(self):
        item = I2CSeqItem("smbus_ara_item")
        item.addr = 0x0C
        item.rw = 1
        item.burst_len = 1
        item.is_ara = True
        item.alert_pending = True
        item.data_tx = [0x50]
        await self.start_item(item)
        await self.finish_item(item)

class SMBusArpSeq(I2CBaseSeq):
    async def body(self):
        # 1. Prepare to ARP (0x01 to 0x61)
        p_arp = I2CSeqItem("prepare_to_arp")
        p_arp.addr = 0x61
        p_arp.rw = 0
        p_arp.burst_len = 1
        p_arp.data_tx = [0x01]
        p_arp.is_arp = True
        p_arp.arp_cmd = 0x01
        await self.start_item(p_arp)
        await self.finish_item(p_arp)

        # 2. Get UDID General (0x02 to 0x61)
        g_udid = I2CSeqItem("get_udid_gen")
        g_udid.addr = 0x61
        g_udid.rw = 0
        g_udid.burst_len = 1
        g_udid.data_tx = [0x02]
        g_udid.is_arp = True
        g_udid.arp_cmd = 0x02
        await self.start_item(g_udid)
        await self.finish_item(g_udid)

        # Read 16-byte UDID
        rd_udid = I2CSeqItem("read_udid_16b")
        rd_udid.addr = 0x61
        rd_udid.rw = 1
        rd_udid.burst_len = 16
        rd_udid.is_arp = True
        rd_udid.data_tx = [(0xA0 + i) & 0xFF for i in range(16)]
        await self.start_item(rd_udid)
        await self.finish_item(rd_udid)

        # 3. Assign Address (0x03) - Match UDID
        as_valid = I2CSeqItem("assign_addr_valid")
        as_valid.addr = 0x61
        as_valid.rw = 0
        as_valid.is_arp = True
        as_valid.arp_cmd = 0x03
        as_valid.assigned_addr = 0x22
        udid_bytes = [0xA1, 0xB2, 0xC0, 0xDE] + [0x00] * 12
        as_valid.data_tx = [0x03] + udid_bytes + [(0x22 << 1)]
        as_valid.burst_len = len(as_valid.data_tx)
        await self.start_item(as_valid)
        await self.finish_item(as_valid)

        # 4. Assign Address (0x03) - Mismatch UDID Rejection
        as_bad = I2CSeqItem("assign_addr_mismatch")
        as_bad.addr = 0x61
        as_bad.rw = 0
        as_bad.is_arp = True
        as_bad.arp_cmd = 0x03
        as_bad.corrupt_udid = True
        bad_udid = [0xFF, 0xEE, 0xDD, 0xCC] + [0x00] * 12
        as_bad.data_tx = [0x03] + bad_udid + [(0x33 << 1)]
        as_bad.burst_len = len(as_bad.data_tx)
        await self.start_item(as_bad)
        await self.finish_item(as_bad)

        # 5. Get UDID Directed (0x04)
        g_dir = I2CSeqItem("get_udid_dir")
        g_dir.addr = 0x22
        g_dir.rw = 0
        g_dir.burst_len = 1
        g_dir.data_tx = [0x04]
        g_dir.is_arp = True
        g_dir.arp_cmd = 0x04
        await self.start_item(g_dir)
        await self.finish_item(g_dir)

        # 6. Reset Device Directed (0x06)
        r_dir = I2CSeqItem("reset_dev_dir")
        r_dir.addr = 0x22
        r_dir.rw = 0
        r_dir.burst_len = 1
        r_dir.data_tx = [0x06]
        r_dir.is_arp = True
        r_dir.arp_cmd = 0x06
        await self.start_item(r_dir)
        await self.finish_item(r_dir)

        # 7. Reset Device General (0x05)
        r_gen = I2CSeqItem("reset_dev_gen")
        r_gen.addr = 0x61
        r_gen.rw = 0
        r_gen.burst_len = 1
        r_gen.data_tx = [0x05]
        r_gen.is_arp = True
        r_gen.arp_cmd = 0x05
        await self.start_item(r_gen)
        await self.finish_item(r_gen)

class I2CArbitrationLossSeq(I2CBaseSeq):
    async def body(self):
        item = I2CSeqItem("arb_loss_item")
        item.addr = 0x50
        item.rw = 0
        item.burst_len = 1
        item.inject_arb_loss = True
        await self.start_item(item)
        await self.finish_item(item)

class SMBusTimeoutSeq(I2CBaseSeq):
    async def body(self):
        item = I2CSeqItem("timeout_hang_item")
        item.addr = 0x50
        item.rw = 0
        item.burst_len = 1
        item.inject_timeout = True
        await self.start_item(item)
        await self.finish_item(item)

class I2CGeneralCallSeq(I2CBaseSeq):
    async def body(self):
        item = I2CSeqItem("gen_call_item")
        item.addr = 0x00
        item.rw = 0
        item.burst_len = 1
        item.data_tx = [0x04]
        await self.start_item(item)
        await self.finish_item(item)

class I2CRandomSweepSeq(I2CBaseSeq):
    def __init__(self, name="i2c_random_sweep_seq", count=15):
        super().__init__(name)
        self.count = count

    async def body(self):
        for i in range(self.count):
            item = I2CSeqItem(f"random_item_{i}")
            item.addr = random.choice([0x50, 0x50, 0x7E, 0x7F])
            item.rw = random.choice([0, 1])
            item.randomize_data(min_len=1, max_len=8)
            await self.start_item(item)
            await self.finish_item(item)

class I2CComprehensiveRegressionSeq(I2CBaseSeq):
    async def body(self):
        # 1. Baseline Write/Read
        await I2CSingleWriteSeq("seq_single_wr").start(self.sequencer)
        await I2CSingleReadSeq("seq_single_rd").start(self.sequencer)

        # 2. Burst Write & Burst Read
        await I2CBurstWriteSeq("seq_burst_wr").start(self.sequencer)
        await I2CBurstReadSeq("seq_burst_rd").start(self.sequencer)

        # 3. Repeated START Combinations
        await I2CRepeatedStartSeq("seq_rstart").start(self.sequencer)

        # 4. Error Condition: NACK
        await I2CNackSeq("seq_nack").start(self.sequencer)

        # 5. True Clock Stretching (Write + Read at byte 0, mid, last)
        await I2CClockStretchSeq("seq_stretch").start(self.sequencer)

        # 6. SMBus PEC (Single, Burst, Corrupted)
        await SMBusPecSeq("seq_pec").start(self.sequencer)

        # 7. SMBALERT# and ARA Read
        await SMBusAlertAraSeq("seq_alert_ara").start(self.sequencer)

        # 8. Full ARP Protocol suite
        await SMBusArpSeq("seq_arp").start(self.sequencer)

        # 9. Arbitration Loss Detection
        await I2CArbitrationLossSeq("seq_arb").start(self.sequencer)

        # 10. 35ms SCL Low Timeout
        await SMBusTimeoutSeq("seq_timeout").start(self.sequencer)

        # 11. General Call (0x00) Broadcast
        await I2CGeneralCallSeq("seq_gen_call").start(self.sequencer)

        # 12. Randomized Stress Sweeps for Coverage Closure
        await I2CRandomSweepSeq("seq_random_sweep", count=15).start(self.sequencer)
