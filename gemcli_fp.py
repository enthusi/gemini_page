import socket
import ssl
import hashlib

host = "gemini.circumlunar.space"
port = 1965

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

with socket.create_connection((host, port)) as sock:
    with context.wrap_socket(sock, server_hostname=host) as ssock:
        cert_der = ssock.getpeercert(binary_form=True)
        fp = hashlib.sha256(cert_der).hexdigest()
        print("SHA256 cert fingerprint:")
        print(fp)

        request = f"gemini://{host}/\r\n"
        print(">>>", repr(request))
        ssock.sendall(request.encode("utf-8"))

        resp = ssock.recv(4096)
        print("<<<")
        print(resp.decode("utf-8", errors="replace"))
