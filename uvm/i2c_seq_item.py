#==============================================================================
# i2c_seq_item.py
# UVM Sequence Item definition for I2C / SMBus 3.0 Controller
#==============================================================================

from pyuvm import uvm_sequence_item
from enum import Enum, auto
import random

class RStartType(Enum):
    NO_RSTART = 0
    WRITE_THEN_READ = 1
    READ_THEN_WRITE = 2
    WRITE_THEN_WRITE = 3
    READ_THEN_READ = 4

class StretchTarget(Enum):
    NONE = 0
    BYTE_0 = 1
    MIDDLE_BYTE = 2
    LAST_BYTE = 3
    ALL_BYTES = 4

class I2CSeqItem(uvm_sequence_item):
    def __init__(self, name="i2c_seq_item"):
        super().__init__(name)
        # Primary transaction fields
        self.addr = 0x50             # 7-bit slave address
        self.rw = 0                  # 0 = Write, 1 = Read
        self.data_tx = []            # Bytes to transmit
        self.data_rx = []            # Bytes received from DUT
        self.burst_len = 1           # Number of data bytes
        
        # Protocol & Feature variants
        self.is_pec = False          # Expect/Append SMBus PEC CRC-8
        self.corrupt_pec = False     # Corrupt PEC for negative testing
        self.is_arp = False          # ARP sequence
        self.arp_cmd = 0x00          # 0x01..0x06
        self.udid = 0xA1B2C0DE000000000000000000000000 # 128-bit UDID
        self.assigned_addr = 0x20    # Reassigned address
        self.corrupt_udid = False    # Mismatched UDID for rejection test
        self.is_ara = False          # Alert Response Address transaction
        
        # Repeated START
        self.rstart_type = RStartType.NO_RSTART
        self.rstart_addr = 0x50
        self.rstart_rw = 1
        self.rstart_data_tx = []
        self.rstart_burst_len = 1
        self.rstart_data_rx = []
        self.rstart_slv_rx_data = []
        self.in_rstart_phase = False
        
        # Clock Stretching Flow Control (Slave side)
        self.stretch_target = StretchTarget.NONE
        self.stretch_cycles_rx = 0   # Delay before asserting rx_ready
        self.stretch_cycles_tx = 0   # Delay before asserting tx_valid
        
        # Fault Injections
        self.inject_nack = False
        self.inject_arb_loss = False
        self.inject_timeout = False
        self.timeout_hold_cycles = 1800000 # >35ms @ 50MHz
        
        # Output Status / Verification Results
        self.ack_error = False
        self.arb_lost = False
        self.smbus_timeout = False
        self.pec_error = False
        self.slv_pec_error = False
        self.alert_pending = False
        self.slv_rx_data = []

    def randomize_data(self, min_len=1, max_len=8):
        self.burst_len = random.randint(min_len, max_len)
        self.data_tx = [random.randint(0, 255) for _ in range(self.burst_len)]
        # Guard against accidental ARP command collisions on SLAVE_ADDR
        if self.burst_len > 0 and 0x01 <= self.data_tx[0] <= 0x06 and not self.is_arp:
            self.data_tx[0] = 0x50

    def __str__(self):
        dir_str = "READ" if self.rw == 1 else "WRITE"
        data_hex = [f"0x{b:02x}" for b in self.data_tx]
        return f"[{self.get_name()}] {dir_str} Addr=0x{self.addr:02x} Len={self.burst_len} Data={data_hex} PEC={self.is_pec}"
