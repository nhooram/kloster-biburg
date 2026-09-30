# usage: python3 bl.py file.py   (or stdin). Sets `result` in code to return data.
import socket, json, sys
code = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
s = socket.create_connection(("127.0.0.1", 9876)); s.settimeout(600)
s.sendall(json.dumps({"type": "execute", "code": code, "strict_json": False}).encode() + b"\0")
buf = b""
while True:
    c = s.recv(1 << 20)
    if not c: break
    buf += c
    if buf.endswith(b"\0"): break
r = json.loads(buf.rstrip(b"\0"))
print(json.dumps(r)[:6000])
