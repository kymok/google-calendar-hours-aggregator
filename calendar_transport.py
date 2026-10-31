"""Calendar HTTPS transport with fallback between IP address families."""

import socket

import httplib2


class FallbackHTTPSConnection(httplib2.HTTPSConnectionWithTimeout):
    def connect(self):
        if self.proxy_info and self.proxy_info.isgood() and self.proxy_info.applies_to(self.host):
            return super().connect()

        addresses = socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM)
        # Try the other family next instead of waiting through every IPv6 address.
        if addresses:
            first, *remaining = addresses
            addresses = [first] + sorted(remaining, key=lambda item: item[0] == first[0])

        last_error = OSError("No addresses found for Calendar API host")
        for family, kind, protocol, _, address in addresses:
            sock = socket.socket(family, kind, protocol)
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(min(5, self.timeout) if self.timeout is not None else 5)
                sock.connect(address)
            except OSError as error:
                sock.close()
                last_error = error
                continue

            try:
                sock.settimeout(self.timeout)
                self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
            except Exception:
                sock.close()
                raise
            return
        raise last_error


class CalendarHttp(httplib2.Http):
    def request(self, uri, method="GET", body=None, headers=None,
                redirections=httplib2.DEFAULT_MAX_REDIRECTS, connection_type=None):
        if connection_type is None and uri.startswith("https://"):
            connection_type = FallbackHTTPSConnection
        return super().request(
            uri, method=method, body=body, headers=headers,
            redirections=redirections, connection_type=connection_type,
        )
