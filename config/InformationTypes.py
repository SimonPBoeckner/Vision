from dataclasses import dataclass
from typing import List, Dict, Any, Union, TypedDict, Optional

@dataclass(frozen=True)
class Resolution:
    width: int
    height: int
    framerate: List[float]

@dataclass(frozen=True)
class Format(TypedDict):
    fourcc: str
    description: str
    resolutions: List[Resolution]

@dataclass(frozen=True)
class Control(TypedDict):
    name: str
    type: str
    min: int
    max: int
    step: int
    default: int
    current: int

@dataclass(frozen=True)
class DeviceInfo(TypedDict, total=False):
    driver_name: str
    card_type: str
    bus_info: str
    driver_version: str
    capabilities: str

@dataclass(frozen=True)
class DeviceData:
    info: DeviceInfo
    formats: List[Format]
    controls: List[Control]
    error: str