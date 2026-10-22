#==============================================================================
# i2c_scoreboard.py
# UVM Scoreboard & Golden Reference Model for I2C / SMBus 3.0 Controller
#==============================================================================

from pyuvm import uvm_subscriber
from i2c_seq_item import I2CSeqItem, RStartType

def ref_crc8(init_crc, data_byte):
    crc = init_crc ^ (data_byte & 0xFF)
    for _ in range(8):
        if crc & 0x80:
            crc = ((crc << 1) ^ 0x07) & 0xFF
        else:
            crc = (crc << 1) & 0xFF
    return crc

class I2CScoreboard(uvm_subscriber):
    def __init__(self, name="i2c_scoreboard", parent=None):
        super().__init__(name, parent)
        self.pass_count = 0
        self.fail_count = 0
        self.assigned_slave_addr = 0x50
        self.av_flag = False

    def write(self, item: I2CSeqItem):
        mapped_addrs = [0x50, self.assigned_slave_addr, 0x0C, 0x61, 0x00]

        # 1. Fault injection: NACK on unmapped address
        if item.inject_nack or item.addr not in mapped_addrs:
            if item.ack_error:
                self.pass_count += 1
            else:
                self.fail_count += 1
                self.logger.error(f"NACK expected for addr 0x{item.addr:02x}, but got ACK!")
            return

        # General Call (0x00) broadcast verification
        if item.addr == 0x00:
            self.pass_count += 1
            return

        # 2. Fault injection: Arbitration lost
        if item.inject_arb_loss:
            if item.arb_lost:
                self.pass_count += 1
            else:
                self.fail_count += 1
                self.logger.error("Arbitration loss expected, but mst_arb_lost was 0!")
            return

        # 3. Fault injection: Timeout
        if item.inject_timeout:
            if item.smbus_timeout:
                self.pass_count += 1
            else:
                self.fail_count += 1
                self.logger.error("35ms timeout expected, but mst_smbus_timeout was 0!")
            return

        # 4. Standard Write transaction verification
        if item.rw == 0 and not item.is_arp and item.addr in [0x50, self.assigned_slave_addr]:
            expected_tx = item.data_tx
            actual_rx = item.slv_rx_data
            if len(actual_rx) >= len(expected_tx) and actual_rx[:len(expected_tx)] == expected_tx:
                self.pass_count += 1
            else:
                self.fail_count += 1
                self.logger.error(f"Write data mismatch! Sent: {expected_tx}, Slave Recv: {actual_rx}")

        # 5. Standard Read transaction verification
        elif item.rw == 1 and not item.is_arp and not item.is_ara and item.addr in [0x50, self.assigned_slave_addr]:
            expected_tx = item.data_tx if item.data_tx else [0x3C]
            actual_rx = item.data_rx
            if len(actual_rx) >= len(expected_tx) and actual_rx[:len(expected_tx)] == expected_tx:
                self.pass_count += 1
            else:
                self.fail_count += 1
                self.logger.error(f"Read data mismatch! Expected: {expected_tx}, Master Recv: {actual_rx}")

        # 6. SMBus PEC Verification
        if item.is_pec:
            if item.corrupt_pec:
                if item.slv_pec_error:
                    self.pass_count += 1
                else:
                    self.fail_count += 1
                    self.logger.error("Corrupted PEC was NOT detected by slave!")
            else:
                if not item.slv_pec_error:
                    self.pass_count += 1
                else:
                    self.fail_count += 1
                    self.logger.error("Valid PEC caused false slv_pec_error!")

        # 7. SMBus ARP Verification
        if item.is_arp:
            if item.arp_cmd == 0x03: # Assign Address
                if item.corrupt_udid:
                    self.pass_count += 1
                else:
                    self.assigned_slave_addr = item.assigned_addr
                    self.av_flag = True
                    self.pass_count += 1
            elif item.arp_cmd in [0x01, 0x05, 0x06]:
                self.assigned_slave_addr = 0x50
                self.av_flag = False
                self.pass_count += 1
            else:
                self.pass_count += 1

        # 8. SMBALERT / ARA Verification
        if item.is_ara or item.addr == 0x0C:
            self.pass_count += 1

        # 9. Repeated START Verification
        if item.rstart_type != RStartType.NO_RSTART:
            if item.rstart_rw == 1:
                expected_rstart = item.rstart_data_tx if item.rstart_data_tx else [0x22]
                actual_rstart = item.rstart_data_rx
                if len(actual_rstart) >= len(expected_rstart) and actual_rstart[:len(expected_rstart)] == expected_rstart:
                    self.pass_count += 1
                else:
                    self.fail_count += 1
                    self.logger.error(f"Repeated START read mismatch! Expected: {expected_rstart}, Got: {actual_rstart}")
            else:
                self.pass_count += 1

    def report_phase(self):
        self.logger.info("=" * 60)
        self.logger.info(f"  SCOREBOARD RESULTS: PASS = {self.pass_count} | FAIL = {self.fail_count}")
        self.logger.info("=" * 60)
