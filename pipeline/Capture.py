from abc import ABC, abstractmethod
from config.DataTypes import FrameData
from config.Config import ConfigStore
import cv2 as cv
import sys
import time
import dataclasses
from typing import Optional

class Capture(ABC):
    """"""

    @abstractmethod
    def get_frame(self, config_store: ConfigStore) -> Optional[FrameData]:
        pass

    @staticmethod
    def config_changed(config_a: ConfigStore, config_b: ConfigStore) -> bool:
        if config_a == None and config_b ==  None:
            return False
        if config_a == None or config_b == None:
            return True
        
        remote_a = config_a.remote_config
        remote_b = config_b.remote_config

        return (
            remote_a.camera_id != remote_b.camera_id
            or remote_a.camera_resolution_width != remote_b.camera_resolution_width
            or remote_a.camera_resolution_height != remote_b.camera_resolution_height
            or remote_a.camera_auto_exposure != remote_b.camera_auto_exposure
            or remote_a.camera_exposure != remote_b.camera_exposure
            or remote_a.camera_gain != remote_b.camera_gain
            or remote_a.camera_denoise != remote_b.camera_denoise
        )
    
class DefaultCapture(Capture):
    """"""

    cap = None
    last_config: ConfigStore

    def get_frame(self, config_store: ConfigStore) -> Optional[FrameData]:
        if self.cap is not None and self.config_changed(self.last_config, config_store):
            print("Restarting capture session")
            self.cap.release()
            self.cap = None

        if self.cap is None:
            self.video = cv.VideoCapture(config_store.remote_config.camera_id)
            self.video.set(cv.CAP_PROP_FRAME_WIDTH, config_store.remote_config.camera_resolution_width)
            self.video.set(cv.CAP_PROP_FRAME_HEIGHT, config_store.remote_config.camera_resolution_height)
            self.video.set(cv.CAP_PROP_AUTO_EXPOSURE, config_store.remote_config.camera_auto_exposure)
            self.video.set(cv.CAP_PROP_EXPOSURE, config_store.remote_config.camera_exposure)
            self.video.set(cv.CAP_PROP_GAIN, int(config_store.remote_config.camera_gain))

        self.last_config = config_store

        retval, frame = self.video.read()
        ts = time.perf_counter()
        return FrameData(retval, frame, ts)

class GStreamerCapture(Capture):
    """"""

    cap = None
    last_config: ConfigStore

    def get_frame(self, config_store: ConfigStore) -> Optional[FrameData]:
        if self.cap is not None and self.config_changed(self.last_config, config_store):
            print("Config changed, stopping capture session")
            self.cap.release()
            self.cap = None
            time.sleep(2)

        if self.cap is None :
            if config_store.remote_config.camera_id == "":
                print("No camera ID, waiting to start capture session")
            else:
                print("Starting capture session")
                self.cap = cv.VideoCapture(
                    "v4l2src device=" + str(config_store.remote_config.camera_id) + ' extra_controls="c,exposure_auto='
                    + str(config_store.remote_config.camera_auto_exposure) + ",exposure_absolute="
                    + str(config_store.remote_config.camera_exposure) + ",gain="
                    + str(int(config_store.remote_config.camera_gain)) + ',sharpness=0,brightness=0" ! image/jpeg, format=MJPG, width='
                    + str(config_store.remote_config.camera_resolution_width) + ", height="
                    + str(config_store.remote_config.camera_resolution_height) + ", framerate="
                    + str(config_store.remote_config.camera_framerate) + " ! jpegdec ! video/x-raw, format=GRAY8 ! appsink drop=true sync=false max-buffers=1",
                    cv.CAP_GSTREAMER,
                )
                print("Capture session ready")

        self.last_config = ConfigStore(
            dataclasses.replace(config_store.local_config), dataclasses.replace(config_store.remote_config)
        )

        if self.cap is not None:
            retval, frame = self.cap.read()
            if not retval:
                print("Capture session failed, restarting")
                self.cap.release()
                self.cap = None # Force reconnect
                sys.exit(1)
            ts = time.perf_counter()
            return FrameData(retval, frame, ts)
        
CAPTURE_IMPLS = {
    "default":DefaultCapture,
    "gstreamer":GStreamerCapture
}