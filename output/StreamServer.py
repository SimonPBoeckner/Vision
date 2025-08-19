from abc import ABC, abstractmethod
import cv2 as cv
import random
import socketserver
import string
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from typing import Dict
from PIL import Image

CLIENT_COUNTS: Dict[str, int] = {}

class StreamServer(ABC):
    """Interface for outputting camera frames."""

    @abstractmethod
    def start(self, port: int) -> None:
        """Starts the output stream."""
        pass

    @abstractmethod
    def set_frame(self, frame: cv.Mat) -> None:
        """Sets the frame to serve."""
        pass

class MjpegServer(StreamServer):
    """MJPEG server for streaming camera frames over HTTP."""
    frame: cv.Mat
    has_frame: bool = False
    uuid: str = ""

    def make_handler(self_mjpeg, uuid: str): # type: ignore
        class StreamingHandler(BaseHTTPRequestHandler):
            HTML = """
    <html>
        <head>
            <title>Northstar Debug</title>
            <style>
                body {
                    background-color: black;
                }

                img {
                    position: absolute;
                    left: 50%;
                    top: 50%;
                    transform: translate(-50%, -50%);
                    max-width: 100%;
                    max-height: 100%;
                }
            </style>
        </head>
        <body>
            <img src="stream.mjpg" />
        </body>
    </html>
            """

            def do_GET(self):
                global CLIENT_COUNTS
                if self.path == "/":
                    content = self.HTML.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                elif self.path == "/stream.mjpg":
                    self.send_response(200)
                    self.send_header("Age", "0")
                    self.send_header("Cache-Control", "no-cache, private")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
                    self.end_headers()
                    try:
                        CLIENT_COUNTS[uuid] += 1
                        while True:
                            if not self_mjpeg.has_frame:
                                time.sleep(0.1)
                            else:
                                pil_im = Image.fromarray(self_mjpeg.frame)
                                stream = BytesIO()
                                pil_im.save(stream, format="JPEG")
                                frame_data = stream.getvalue()

                                self.wfile.write(b"--FRAME\r\n")
                                self.send_header("Content-Type", "image/jpeg")
                                self.send_header("Content-Length", str(len(frame_data)))
                                self.end_headers()
                                self.wfile.write(frame_data)
                                self.wfile.write(b"\r\n")
                    except Exception as e:
                        print("Removed streaming client %s: %s", self.client_address, str(e))
                    finally:
                        CLIENT_COUNTS[uuid] -= 1
                else:
                    self.send_error(404)
                    self.end_headers()

        return StreamingHandler
    
    class StreamingServer(socketserver.ThreadingMixIn, HTTPServer):
        allow_reuse_address = True
        daemon_threads = True

    def run(self, port: int) -> None:
        self.uuid = "".join(random.choice(string.ascii_lowercase) for i in range(12))
        CLIENT_COUNTS[self.uuid] = 0
        server = self.StreamingServer(("", port), self.make_handler(self.uuid))
        server.serve_forever()

    def start(self, port: int) -> None:
        threading.Thread(target=self.run, daemon=True, args=(port,)).start()

    def set_frame(self, frame: cv.Mat) -> None:
        self.frame = frame
        self.has_frame = True

    def get_client_count(self) -> int:
        if len(self.uuid) > 0:
            return CLIENT_COUNTS[self.uuid]
        else:
            return 0