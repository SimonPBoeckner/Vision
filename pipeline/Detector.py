from abc import ABC, abstractmethod
from config.DataTypes import FrameData, FiducialData
from typing import List
import cv2 as cv

class Detector(ABC):
    """"""

    @abstractmethod
    def detect_tag(self, frame_data: FrameData) -> List[FiducialData]:
        pass

class ArucoDetector(Detector):
    """"""

    def __init__(self, dict_id):
        self.aruco_dict = cv.aruco.getPredefinedDictionary(dict_id)
        self.aruco_params = cv.aruco.DetectorParameters()

    def detect_tag(self, frame_data: FrameData) -> List[FiducialData]:
        corners, ids, _ = cv.aruco.detectMarkers(frame_data.frame, self.aruco_dict, parameters=self.aruco_params)
        if ids is None or len(corners) == 0:
            return []
        return [FiducialData(id[0], corner, frame_data.timestamp) for id, corner in zip(ids, corners)]