from abc import ABC, abstractmethod
from config.Config import ConfigStore

import ntcore

class CalibrationCommandSource(ABC):
    """
    Abstract base class for calibration command sources.
    This class defines the interface for obtaining calibration commands
    and flags from various sources, such as NetworkTables.
    """

    @abstractmethod
    def get_calibrating(self, config_store: ConfigStore) -> bool:
        pass

    @abstractmethod
    def get_capture_flag(self, config_store: ConfigStore) -> bool:
        pass
    
    
class NTCalibrationCommandSource(CalibrationCommandSource):
    """
    NetworkTables-based implementation of CalibrationCommandSource.
    This class uses NetworkTables to manage calibration state and capture flags.
    """

    init_complete: bool = False
    active_entry: ntcore.BooleanEntry
    capture_flag_entry: ntcore.BooleanEntry

    def _init(self, config_store: ConfigStore):
        if not self.init_complete:
            nt_table = ntcore.NetworkTableInstance.getDefault().getTable(
                "/" + config_store.local_config.device_id + "/calibration"
            )
            self.active_entry = nt_table.getBooleanTopic("active").getEntry(False)
            self.capture_flag_entry = nt_table.getBooleanTopic("capture_flag").getEntry(False)
            self.active_entry.set(False)
            self.capture_flag_entry.set(False)
            self.init_complete = True

    def get_calibrating(self, config_store: ConfigStore) -> bool:
        self._init(config_store)
        calibrating = self.active_entry.get()
        if not calibrating:
            self.capture_flag_entry.set(False)
        return calibrating
    
    def get_capture_flag(self, config_store: ConfigStore) -> bool:
        self._init(config_store)
        if self.capture_flag_entry.get():
            self.capture_flag_entry.set(False)
            return True
        return False