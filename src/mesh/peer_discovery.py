import random
import hashlib
import time
import socket

class PeerDiscovery:
    def __init__(self, mesh_address, mesh_port):
        self.mesh_address = mesh_address
        self.mesh_port = mesh_port
        self.peers = set()
        self.last_discovery = 0

    def discover_peers(self):
        if time.time() - self.last_discovery < 60:
            return
        self.last_discovery = time.time()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f'MoodMix-Discover-{hashlib.sha256(str(random.randint(0, 1000000)).encode()).hexdigest()}'
        sock.sendto(message.encode(), ('255.255.255.255', self.mesh_port))

        while True:
            try:
                data, addr = sock.recvfrom(1024)
                if data.decode().startswith('MoodMix-Peer-'):
                    peer_id = data.decode().split('-')[2]
                    self.peers.add(peer_id)
            except socket.timeout:
                break

    def get_peers(self):
        self.discover_peers()
        return self.peers
