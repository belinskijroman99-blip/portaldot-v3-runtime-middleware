import socket

SYS_GATEWAY_STATUS = {"vpn_active": True}
raw_packet_sent_bytes = 0

class NetworkLayerException(Exception): pass

_orig_socket = socket.socket
_orig_getaddrinfo = socket.getaddrinfo

def hooked_getaddrinfo(host, port, *args, **kwargs):
    global raw_packet_sent_bytes
    if not SYS_GATEWAY_STATUS.get("vpn_active", False):
        raw_packet_sent_bytes = 0
        raise NetworkLayerException("L4 Socket Kill Switch: VPN inactive")
    if host not in ("127.0.0.1", "localhost", "::1"):
        return _orig_getaddrinfo("127.0.0.1", port, *args, **kwargs)
    return _orig_getaddrinfo(host, port, *args, **kwargs)

class HookedSocket(_orig_socket):
    def connect(self, address):
        global raw_packet_sent_bytes
        if not SYS_GATEWAY_STATUS.get("vpn_active", False):
            raw_packet_sent_bytes = 0
            self.close()
            raise NetworkLayerException("L4 Socket Kill Switch: VPN inactive")
        return super().connect(address)

    def send(self, data, *args, **kwargs):
        global raw_packet_sent_bytes
        if not SYS_GATEWAY_STATUS.get("vpn_active", False):
            raw_packet_sent_bytes = 0
            self.close()
            raise NetworkLayerException("L4 Socket Kill Switch: VPN inactive")
        sent = super().send(data, *args, **kwargs)
        raw_packet_sent_bytes += sent
        return sent

def install_kill_switch():
    socket.socket = HookedSocket
    socket.getaddrinfo = hooked_getaddrinfo

def uninstall_kill_switch():
    socket.socket = _orig_socket
    socket.getaddrinfo = _orig_getaddrinfo
