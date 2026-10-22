#==============================================================================
# i2c_env.py
# UVM Environment connecting Sequencer, Drivers, Monitors, Scoreboard, & Coverage
#==============================================================================

from pyuvm import uvm_env, uvm_sequencer
from i2c_seq_item import I2CSeqItem
from i2c_master_driver import I2CMasterDriver
from i2c_slave_driver import I2CSlaveDriver
from i2c_bus_monitor import I2CBusMonitor
from i2c_scoreboard import I2CScoreboard
from i2c_coverage import I2CCoverage

class I2CEnv(uvm_env):
    def __init__(self, name="i2c_env", parent=None):
        super().__init__(name, parent)
        self.sequencer = None
        self.master_driver = None
        self.slave_driver = None
        self.bus_monitor = None
        self.scoreboard = None
        self.coverage = None

    def build_phase(self):
        super().build_phase()
        self.sequencer = uvm_sequencer("sequencer", self)
        self.master_driver = I2CMasterDriver("master_driver", self)
        self.slave_driver = I2CSlaveDriver("slave_driver", self)
        self.bus_monitor = I2CBusMonitor("bus_monitor", self)
        self.scoreboard = I2CScoreboard("scoreboard", self)
        self.coverage = I2CCoverage("coverage", self)

    def connect_phase(self):
        super().connect_phase()
        # Connect master sequencer to master driver
        self.master_driver.seq_item_port.connect(self.sequencer.seq_item_export)

        # Connect bus monitor to coverage subscriber
        self.bus_monitor.ap.connect(self.coverage.analysis_export)

        # Hook slave driver to active items for reactive flow control
        orig_drive = self.master_driver.drive_item
        async def drive_item_hook(item):
            self.slave_driver.set_active_item(item)
            await orig_drive(item)
            # Direct sample into scoreboard & coverage for host-level verification
            self.scoreboard.write(item)
            self.coverage.write(item)

        self.master_driver.drive_item = drive_item_hook
