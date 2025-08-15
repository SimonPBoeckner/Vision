from dataclasses import dataclass
from typing import List, Optional, Sequence
import numpy as np
import cv2 as cv
import numpy.typing
from wpimath.geometry import Pose3d

@dataclass
class FrameData:
    retval: bool
    frame: np.ndarray
    timestamp: float

@dataclass
class FiducialData:
    id: int
    corners: cv.typing.MatLike
    timestamp: float

@dataclass
class PoseData:
    tag_ids: List[int]
    pose: Pose3d
    error: float
    timestamp: float