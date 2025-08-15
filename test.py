from config.ConfigSource import FileConfigSource
from config.Config import ConfigStore, LocalConfig, RemoteConfig

config_store = ConfigStore(LocalConfig(), RemoteConfig())
fileconfig_source = FileConfigSource("/home/sim/development/config/config.json", "/home/sim/development/config/camera_calibration.json")

fileconfig_source.update(config_store)

print(config_store.local_config.camera_matrix)