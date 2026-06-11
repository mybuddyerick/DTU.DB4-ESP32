import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 80)) 
s.listen(5)

print("Web server initialized and listening on port 80...")

while True:
    try:
        conn, addr = s.accept()
        print('Got a browser request from %s' % str(addr))
        request = conn.recv(1024)
        
        with open('index.html', 'r') as f:
            html_page = f.read()
        
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        
        conn.sendall(html_page)
        conn.close()
    except Exception as e:
        print("An error occurred inside the server loop:", e)