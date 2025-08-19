from dataclasses import dataclass
from typing import List, Union
import numpy as np
import numpy.typing
import cv2 as cv
from wpimath.geometry import Pose3d

@dataclass(frozen=True)
class FiducialFrameObservation:
    tag_id: int
    corners: cv.typing.MatLike


@dataclass(frozen=True)
class FiducialPoseObservation:
    tag_id: int
    pose_0: Pose3d
    error_0: float
    pose_1: Pose3d
    error_1: float


@dataclass(frozen=True)
class CameraPoseObservation:
    tag_ids: List[int]
    pose_0: Pose3d
    error_0: float
    pose_1: Union[Pose3d, None]
    error_1: Union[float, None]


@dataclass(frozen=True)
class TagAngleObservation:
    tag_id: int
    corners: numpy.typing.NDArray[np.float64]
    distance: float