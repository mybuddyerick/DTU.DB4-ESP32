import socket
import binascii
import hashlib

try:
    import ujson as json
except ImportError:
    import json

class WebSocketServer:
    def __init__(self, port=81):
        self.port = port
        self.server_socket = None
        self.clients = []
        self.running = False

    def start(self):
        self.stop()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.port))
        self.server_socket.listen(5)
        
        try:
            self.server_socket.setblocking(False)
        except Exception:
            self.server_socket.settimeout(0)
            
        self.running = True
        print("WebSocket server initialized on port", self.port)

    def stop(self):
        self.running = False
        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except Exception:
                pass
        
        for client in self.clients:
            try:
                client.close()
            except Exception:
                pass
                
        self.server_socket = None
        self.clients = []

    def _handshake(self, conn, req):
        lines = req.split(b"\r\n")
        key = None
        for line in lines:
            if line.lower().startswith(b"sec-websocket-key:"):
                key = line.split(b":", 1)[1].strip()
                break
                
        if not key:
            conn.close()
            return False

        magic = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        digest = hashlib.sha1(key + magic).digest()
        accept_key = binascii.b2a_base64(digest).strip()

        response = (
            b"HTTP/1.1 101 Switching Protocols\r\n"
            b"Upgrade: websocket\r\n"
            b"Connection: Upgrade\r\n"
            b"Sec-WebSocket-Accept: " + accept_key + b"\r\n\r\n"
        )
        conn.send(response)
        return True

    def update(self):
        if not self.running or self.server_socket is None:
            return

        try:
            conn, addr = self.server_socket.accept()
            req = conn.recv(1024)
            
            if b"Upgrade: websocket" in req:
                if self._handshake(conn, req):
                    try:
                        conn.setblocking(False)
                    except Exception:
                        conn.settimeout(0)
                    self.clients.append(conn)
                    print("New WebSocket client connected from", addr)
            else:
                conn.close()
        except OSError:
            pass

    def broadcast(self, data_dict):
        """
        Takes a Python dictionary, converts it to JSON, 
        and pushes it directly to all active clients.
        """
        if not self.clients:
            return

        try:
            msg = json.dumps(data_dict).encode("utf-8")
        except Exception:
            return

        length = len(msg)
        if length <= 125:
            header = bytearray([0x81, length])
        elif length <= 65535:
            header = bytearray([0x81, 126, (length >> 8) & 0xFF, length & 0xFF])
        else:
            return

        frame = header + msg
        
        active_clients = []
        for client in self.clients:
            try:
                client.send(frame)
                active_clients.append(client)
            except OSError:
                try:
                    client.close()
                except Exception:
                    pass
        
        self.clients = active_clients
