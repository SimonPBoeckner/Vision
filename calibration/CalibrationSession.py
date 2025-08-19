import datetime
import os
from typing import List

import cv2 as cv
import numpy as np
from config.ConfigSource import FileConfigSource

class CalibrationSession:
    """
    Class to handle the calibration session for camera calibration using ArUco markers.
    This class manages the detection of ArUco markers, saving calibration data,
    and finalizing the calibration process.
    It uses OpenCV's ArUco module to detect markers and perform camera calibration.
    """
    all_charuco_corners: List[np.ndarray] = []
    all_charuco_ids: List[np.ndarray] = []
    imsize = None

    NEW_CALIBRATION_FILENAME = "calibration_new.yml"

    def __init__(self) -> None:
        self.aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_1000)
        self.aruco_params = cv.aruco.DetectorParameters()
        self.charuco_board = cv.aruco.CharucoBoard((12, 9), 0.030, 0.023, self.aruco_dict)

    def process_frame(self, frame: cv.Mat, save: bool) -> None:
        # Get image size
        if self.imsize == None:
            self.imsize = (frame.shape[0], frame.shape[1])

        # Detect tags
        (corners, ids, rejected) = cv.aruco.detectMarkers(frame, self.aruco_dict, parameters=self.aruco_params)
        if len(corners) > 0:
            cv.aruco.drawDetectedMarkers(frame, corners)

            # Find Charuco corners
            (retval, charuco_corners, charuco_ids) = cv.aruco.interpolateCornersCharuco(
                corners, ids, frame, self.charuco_board
            )
            if retval:
                cv.aruco.drawDetectedCornersCharuco(frame, charuco_corners, charuco_ids)

                # Save corners
                if save:
                    self.all_charuco_corners.append(charuco_corners)
                    self.all_charuco_ids.append(charuco_ids)
                    print("Saved calibration frame")

    def finish(self) -> None:
        if len(self.all_charuco_corners) == 0:
            print("ERROR: No calibration data")
            return
        
        if os.path.exists(self.NEW_CALIBRATION_FILENAME):
            os.remove(self.NEW_CALIBRATION_FILENAME)

        (retval, camera_matrix, distortion_coefficients, rvecs, tvecs) = cv.aruco.calibrateCameraCharuco(
            self.all_charuco_corners, self.all_charuco_ids, self.charuco_board, self.imsize, None, None
        )

        if retval:
            calibration_store = cv.FileStorage(self.NEW_CALIBRATION_FILENAME, cv.FILE_STORAGE_WRITE)
            calibration_store.write("calibration_date", str(datetime.datetime.now()))
            calibration_store.write("camera_resolution", self.imsize)
            calibration_store.write("camera_matrix", camera_matrix)
            calibration_store.write("distortion_coefficients", distortion_coefficients)
            calibration_store.release()
            print("Calibration finished")
        else:
            print("ERROR: Calibration failed")