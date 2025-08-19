import math
from typing import List
import numpy as np
import numpy.typing
import cv2 as cv
from wpimath.geometry import Pose3d, Translation3d, Rotation3d

def opencv_pose_to_wpilib(tvec: cv.typing.MatLike, rvec: cv.typing.MatLike) -> Pose3d:
    return Pose3d(
        Translation3d(tvec[2][0], -tvec[0][0], -tvec[1][0]),
        Rotation3d(
            np.array([rvec[2][0], -rvec[0][0], -rvec[1][0]]),
            math.sqrt(math.pow(rvec[0][0], 2) + math.pow(rvec[1][0], 2) + math.pow(rvec[2][0], 2)),
        ),
    )

def wpilib_translation_to_opencv(translation: Translation3d) -> List[float]:
    return [-translation.Y(), -translation.Z(), translation.X()]