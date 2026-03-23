import asyncio
from typing import Dict, Set, Optional
import socket
import json
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser
from kademlia.network import Server

class PeerDiscovery:
    def __init__(self, port: int = 8468):
        self.port = port
        self.peers: Set[str] = set()
        self.node_id = self._generate_node_id()
        self.zeroconf = Zeroconf()
        self.dht_server: Optional[Server] = None
        self.service_name = '_swarmnet._tcp.local.'
        
    def _generate_node_id(self) -> str:
        """Generate unique node identifier"""
        return f"{socket.gethostname()}-{self.port}"
        
    async def start(self):
        """Initialize peer discovery services"""
        # Start mDNS service
        info = ServiceInfo(
            self.service_name,
            f"{self.node_id}.{self.service_name}",
            addresses=[socket.inet_aton(self._get_local_ip())],
            port=self.port,
            properties={"node_id": self.node_id}
        )
        self.zeroconf.register_service(info)
        
        # Start DHT server
        self.dht_server = Server()
        await self.dht_server.listen(self.port + 1)
        
        # Bootstrap DHT if bootstrap nodes are known
        bootstrap_nodes = [("bootstrap.swarmnet", 8468)]
        await self.dht_server.bootstrap(bootstrap_nodes)
        
    def _get_local_ip(self) -> str:
        """Get local non-loopback IP address"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    async def advertise_peer(self, metadata: Dict):
        """Advertise peer presence with metadata"""
        key = f"peer:{self.node_id}"
        value = json.dumps({
            "node_id": self.node_id,
            "ip": self._get_local_ip(),
            "port": self.port,
            "metadata": metadata
        })
        await self.dht_server.set(key, value)

    async def discover_peers(self) -> Set[str]:
        """Discover available peers in the network"""
        discovered = set()
        # Query DHT for peers
        async def query_peer(key_prefix: str):
            for key in await self.dht_server.get_keys(key_prefix):
                value = await self.dht_server.get(key)
                if value:
                    peer_data = json.loads(value)
                    discovered.add(peer_data["node_id"])
                    self.peers.add(peer_data["node_id"])
        
        await query_peer("peer:")
        return discovered

    async def stop(self):
        """Cleanup and stop peer discovery"""
        if self.dht_server:
            self.dht_server.stop()
        self.zeroconf.close()

    async def get_peer_info(self, peer_id: str) -> Optional[Dict]:
        """Get detailed information about a specific peer"""
        key = f"peer:{peer_id}"
        value = await self.dht_server.get(key)
        if value:
            return json.loads(value)
        return None