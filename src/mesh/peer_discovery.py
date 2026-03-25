import random
import asyncio
import websockets

class PeerDiscovery:
    def __init__(self, mesh_address, mesh_port):
        self.mesh_address = mesh_address
        self.mesh_port = mesh_port
        self.peers = set()
        self.discovery_task = None

    async def start_discovery(self):
        self.discovery_task = asyncio.create_task(self.discover_peers())
        await self.discovery_task

    async def discover_peers(self):
        while True:
            # Discover new peers
            new_peers = await self.find_new_peers()
            self.peers.update(new_peers)

            # Connect to new peers
            await self.connect_to_peers(new_peers)

            # Wait for a random interval before the next discovery cycle
            await asyncio.sleep(random.uniform(10, 30))

    async def find_new_peers(self):
        async with websockets.connect(f'ws://{self.mesh_address}:{self.mesh_port}/peers') as websocket:
            # Request a list of known peers from the mesh network
            await websocket.send('GET_PEERS')
            peer_addresses = await websocket.recv()

        new_peers = set()
        for peer_address in peer_addresses.split(','):
            if peer_address not in self.peers:
                new_peers.add(peer_address)

        return new_peers

    async def connect_to_peers(self, new_peers):
        for peer_address in new_peers:
            try:
                async with websockets.connect(f'ws://{peer_address}/connect') as websocket:
                    # Perform handshake and establish connection with the new peer
                    await websocket.send('HELLO')
                    response = await websocket.recv()
                    if response == 'WELCOME':
                        print(f'Connected to new peer: {peer_address}')
            except websockets.exceptions.ConnectionError:
                print(f'Failed to connect to peer: {peer_address}')
