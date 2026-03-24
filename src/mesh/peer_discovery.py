import socket
import struct
import time

MDNS_ADDR = '224.0.0.251'
MDNS_PORT = 5353

def discover_peers():
    """Discover other MoodMix peers on the local network using multicast DNS."""
    peers = []

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Join the multicast group
    group = socket.inet_aton(MDNS_ADDR)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Send the multicast query
    message = b'\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x05_mood\x05_tcp\x05local\x00\x00\x0c\x00\x01'
    sock.sendto(message, (MDNS_ADDR, MDNS_PORT))

    # Wait for responses
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            peers.append(addr[0])
        except socket.timeout:
            break

    # Leave the multicast group
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
    sock.close()

    return peers
