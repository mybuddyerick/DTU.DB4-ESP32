import socket
import os
import gc

try:
    import ujson as json
except ImportError:
    import json

from time import ticks_ms, ticks_diff


PORT = 80
CHUNK_SIZE = 1024

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".csv": "text/csv; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",

    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}

BLOCKED_ROOT_FILES = {
    "boot.py",
    "main.py",
    ".DS_Store",
}


def get_extension(filename):
    dot = filename.rfind(".")

    if dot == -1:
        return ""

    return filename[dot:].lower()


def is_safe_path(path):
    if ".." in path:
        return False

    if path.startswith("/"):
        return False

    if path == "":
        return False

    parts = path.split("/")
    for part in parts:
        if part == "" or part.startswith("."):
            return False

    return True


def map_url_to_file(url_path):
    url_path = url_path.split("?", 1)[0]

    if url_path == "/":
        return "/site/index.html"

    # Remove first slash
    path = url_path.lstrip("/")

    if path in BLOCKED_ROOT_FILES:
        return None

    # Allow CSV, JSON and TXT files from /data
    if path.startswith("data/"):
        if not is_safe_path(path):
            return None

        ext = get_extension(path)

        # Keep data public, but limited
        if ext not in [".csv", ".json", ".txt"]:
            return None

        return "/" + path

    if path.startswith("control/"):
        return None

    if not is_safe_path(path):
        return None

    return "/site/" + path


def get_url_path(request):
    try:
        request = request.decode("utf-8", "ignore")
        first_line = request.split("\r\n")[0]
        parts = first_line.split(" ")

        if len(parts) < 2:
            return "/"

        return parts[1]

    except Exception:
        return "/"


def safe_getattr(obj, name, default=None):
    try:
        if obj is None:
            return default

        return getattr(obj, name, default)

    except Exception:
        return default


def safe_call(obj, name, default=None):
    try:
        if obj is None:
            return default

        method = getattr(obj, name, None)

        if method is None:
            return default

        return method()

    except Exception:
        return default


def dict_value(values, key, default=None):
    try:
        if values is None:
            return default

        return values.get(key, default)

    except Exception:
        return default


def memory_free():
    try:
        return gc.mem_free()
    except Exception:
        return None


class WebServer:
    def __init__(
        self,
        port=PORT,
        rgb_sensor=None,
        temperature=None,
        pumps=None,
        peltier=None,
        status_func=None,
        latest_rgb_func=None
    ):
        self.port = port

        self.rgb_sensor = rgb_sensor
        self.temperature = temperature
        self.pumps = pumps
        self.peltier = peltier

        # Optional custom full-status provider
        self.status_func = status_func

        # Kept for compatibility with old code
        self.latest_rgb_func = latest_rgb_func

        self.server_socket = None
        self.running = False
        self.start_time_ms = ticks_ms()

    def start(self):
        self.stop()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.port))
        self.server_socket.listen(3)

        try:
            self.server_socket.setblocking(False)
        except Exception:
            self.server_socket.settimeout(0)

        self.running = True

        print("Web server initialized on port", self.port)

    def stop(self):
        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except Exception:
                pass

        self.server_socket = None
        self.running = False

    def update(self):
        if not self.running or self.server_socket is None:
            return

        conn = None

        try:
            conn, addr = self.server_socket.accept()
            request = conn.recv(1024)

            url_path = get_url_path(request)

            if url_path.startswith("/api/status"):
                self.send_status(conn)
            elif url_path.startswith("/api/rgb/latest"):
                self.send_latest_rgb(conn)
            else:
                filename = map_url_to_file(url_path)
                self.send_file(conn, filename)

        except OSError:
            # No incoming connection. This is normal in non-blocking mode.
            pass

        except Exception as error:
            print("Web server error:", error)

        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

            gc.collect()

    def send_text(self, conn, status, text, content_type="text/plain; charset=utf-8"):
        body = text.encode("utf-8")

        header = (
            "HTTP/1.1 {}\r\n"
            "Content-Type: {}\r\n"
            "Content-Length: {}\r\n"
            "Cache-Control: no-store\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(status, content_type, len(body))

        conn.send(header.encode("utf-8"))
        conn.send(body)

    def get_latest_rgb(self):
        if self.rgb_sensor is not None:
            return safe_call(self.rgb_sensor, "get_latest", None)

        if self.latest_rgb_func is not None:
            try:
                return self.latest_rgb_func()
            except Exception:
                return None

        return None

    def get_latest_temperature(self):
        return safe_call(self.temperature, "get_latest", None)

    def build_status(self):
        if self.status_func is not None:
            try:
                return self.status_func()
            except Exception as error:
                return {
                    "available": False,
                    "error": "status_func failed",
                    "message": str(error)
                }

        latest_rgb = self.get_latest_rgb()
        latest_temp = self.get_latest_temperature()

        return {
            "available": True,
            "uptime_ms": ticks_diff(ticks_ms(), self.start_time_ms),

            "system": {
                "free_memory": memory_free()
            },

            "rgb": {
                "available": latest_rgb is not None,
                "sensor_enabled": safe_getattr(self.rgb_sensor, "enabled", False),
                "logging": safe_getattr(self.rgb_sensor, "log_enabled", None),
                "time_ms": dict_value(latest_rgb, "time_ms"),
                "clear": dict_value(latest_rgb, "clear"),
                "red": dict_value(latest_rgb, "red"),
                "green": dict_value(latest_rgb, "green"),
                "blue": dict_value(latest_rgb, "blue")
            },

            "temperature": {
                "available": latest_temp is not None,
                "sensor_enabled": safe_getattr(self.temperature, "enabled", False),
                "logging": safe_getattr(self.temperature, "log_enabled", None),
                "time_ms": dict_value(latest_temp, "time_ms"),
                "temp_c": dict_value(latest_temp, "temp_c"),
                "raw_average": dict_value(latest_temp, "raw_average"),
                "voltage": dict_value(latest_temp, "voltage"),
                "resistance": dict_value(latest_temp, "resistance")
            },

            "outputs": {
                "cooler_pump": safe_call(self.pumps, "cooler_running", False),
                "waste_pump": safe_call(self.pumps, "waste_running", False),
                "peltier": safe_call(self.peltier, "running", False)
            }
        }

    def send_status(self, conn):
        status = self.build_status()
        body = json.dumps(status)

        self.send_text(
            conn,
            "200 OK",
            body,
            "application/json; charset=utf-8"
        )

    def send_latest_rgb(self, conn):
        latest = self.get_latest_rgb()

        if latest is None:
            self.send_text(
                conn,
                "200 OK",
                '{"available":false}',
                "application/json; charset=utf-8"
            )
            return

        body = json.dumps({
            "available": True,
            "time_ms": latest["time_ms"],
            "clear": latest["clear"],
            "red": latest["red"],
            "green": latest["green"],
            "blue": latest["blue"]
        })

        self.send_text(
            conn,
            "200 OK",
            body,
            "application/json; charset=utf-8"
        )

    def send_file(self, conn, filename):
        if filename is None:
            self.send_text(conn, "403 Forbidden", "Forbidden")
            return

        ext = get_extension(filename)
        mime = MIME_TYPES.get(ext)

        if mime is None:
            self.send_text(conn, "415 Unsupported Media Type", "Unsupported file type")
            return

        try:
            file_size = os.stat(filename)[6]
        except OSError:
            self.send_text(conn, "404 Not Found", "File not found: " + filename)
            return

        header = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: {}\r\n"
            "Content-Length: {}\r\n"
            "Cache-Control: no-store\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(mime, file_size)

        conn.send(header.encode("utf-8"))

        with open(filename, "rb") as file:
            while True:
                chunk = file.read(CHUNK_SIZE)

                if not chunk:
                    break

                conn.send(chunk)