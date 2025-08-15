from flask import Flask, Response, request, jsonify
from abc import ABC, abstractmethod
import cv2 as cv
import sys
import threading
import time

class StreamServer(ABC):
    """"""
    def __init__(self, host: str="0.0.0.0", port: int=5000) -> None:
        self.host = host
        self.port = port
        self.settings = {}
        self.settings_lock = threading.Lock()

        self.latest_frame = None
        self.frame_lock = threading.Lock()

        self.app = Flask(__name__)

        # Routes
        self.app.add_url_rule('/video', 'video_feed', self._video_feed)
        self.app.add_url_rule('/settings', 'settings', self._handle_settings, methods=['GET', 'POST'])

    @abstractmethod
    def send_frame(self, frame: cv.typing.MatLike) -> None:
        """Receive a frame from the user and make it available for streaming."""

    def _generate_frames(self):
        while True:
            with self.frame_lock:
                frame = self.latest_frame
            if frame is None:
                time.sleep(0.1)
                continue
            ret, buffer = cv.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
    def _video_feed(self):
        return Response(self._generate_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    
    def _handle_settings(self):
        if request.method == 'POST':
            data = request.json
            if not data:
                return jsonify({"error": "No JSON data received"}), 400
            with self.settings_lock:
                self.settings.update(data)
            return jsonify({"status": "Settings updated", "settings": self.settings})
        else:
            with self.settings_lock:
                return jsonify(self.settings)
            
    def run(self):
        self.app.run(host=self.host, port=self.port, threaded=True)

class FlaskStreamServer(StreamServer):
    """"""

    def send_frame(self, frame: cv.typing.MatLike) -> None:
        # Just store the lastest frame for streaming
        with self.frame_lock:
            self.latest_frame = frame