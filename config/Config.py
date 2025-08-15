from dataclasses import dataclass
import cv2 as cv

@dataclass
class LocalConfig:
    device_id: str = ""
    server_ip: str = ""
    apriltags_stream_port: int = 5000
    capture_impl: str = ""
    apriltags_enable: bool = True
    has_calibration: bool = False
    camera_matrix: cv.typing.MatLike = None
    distortion_coefficients: cv.typing.MatLike = None

@dataclass
class RemoteConfig:
    camera_id: str = "/dev/video0"
    camera_resolution_width: int = 1280
    camera_resolution_height: int = 720
    camera_framerate: float = 60/1
    camera_auto_exposure: int = 0
    camera_exposure: int = 0
    camera_gain: float = 0
    camera_denoise: float = 0
    fiducial_size_m: float = 0.1651
    tag_layout: any = None
    timestamp: int = 0

@dataclass
class ConfigStore:
    local_config: LocalConfig
    remote_config: RemoteConfig