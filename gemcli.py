import socket
import ssl

host = "gemini.enthusi.de"
port = 1965

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

with socket.create_connection((host, port)) as sock:
    with context.wrap_socket(sock, server_hostname=host) as ssock:
        request = f"gemini://{host}/\r\n"

        print(">>> SENT BEFORE TLS:")
        print(repr(request))

        ssock.sendall(request.encode("utf-8"))

        print("<<< RECEIVED AFTER TLS:")
        while True:
            data = ssock.recv(4096)
            if not data:
                break
            print(data.decode("utf-8", errors="replace"), end="")
