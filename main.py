import socket
import os
import gc

PORT = 80
CHUNK_SIZE = 1024

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".txt": "text/plain; charset=utf-8",
}

BLOCKED = {
    "boot.py",
    "main.py",
    "pymakr.conf",
    ".DS_Store",
}


def get_extension(filename):
    dot = filename.rfind(".")
    if dot == -1:
        return ""
    return filename[dot:].lower()


def get_path(request):
    try:
        request = request.decode("utf-8", "ignore")
        first_line = request.split("\r\n")[0]
        path = first_line.split(" ")[1]
    except Exception:
        return get_file("index.html")

    path = path.split("?")[0]

    if path == "/":
        return get_file("index.html")

    filename = path.lstrip("/")

    return get_file(filename)

def get_file(file_path):
    # Simple safety rule: only serve files from root folder
    if ("/" in file_path or ".." in file_path) or (file_path in BLOCKED):
        return None

    return f"/site/{file_path}"


def send_text(conn, status, text):
    body = text.encode("utf-8")
    header = (
        "HTTP/1.1 {}\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).format(status, len(body))

    conn.send(header.encode("utf-8"))
    conn.send(body)


def send_file(conn, filename):
    print("Serving:", filename)

    if filename is None:
        send_text(conn, "400 Bad Request", "Bad request")
        return

    if filename in BLOCKED:
        send_text(conn, "403 Forbidden", "Forbidden")
        return

    ext = get_extension(filename)
    mime = MIME_TYPES.get(ext)

    if mime is None:
        send_text(conn, "415 Unsupported Media Type", "Unsupported file type")
        return

    try:
        file_size = os.stat(filename)[6]
    except OSError:
        send_text(conn, "404 Not Found", "File not found: " + filename)
        return

    header = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: {}\r\n"
        "Content-Length: {}\r\n"
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


try:
    server_socket.close()
except Exception:
    pass

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("0.0.0.0", PORT))
server_socket.listen(3)

print("Web server initialized and listening on port 80...")

while True:
    conn = None

    try:
        conn, addr = server_socket.accept()
        request = conn.recv(1024)

        filename = get_path(request)
        send_file(conn, filename)

    except Exception as e:
        print("Server error:", e)

    finally:
        if conn:
            conn.close()
        gc.collect()