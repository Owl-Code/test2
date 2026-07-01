import http.server
import socketserver
import json
import os
import sys
import webbrowser
from typing import Any, Dict, List
from base_graph import HybridControlSwarmGraph, EmergenceNode, ControlMode, EdgeType, AdaptiveEdge, TrophallaxisEdge, EmergenceEdge, Checkpoint
from base_graph.utils.serialization import SwarmStateEncoder

# Keep single global swarm state inside visualization server
swarm = HybridControlSwarmGraph(name="web-visualization-swarm")
checkpoints: Dict[str, Checkpoint] = {}

# Set up some interesting nodes and edges to visualize initially
def initialize_visualization_swarm():
    # 1. Spawns 12 nodes with varying opinions and resources
    nodes_data = [
        ("nest", 100.0, 0.0, ControlMode.EMERGENCE),
        ("node_1", 80.0, 0.2, ControlMode.DECENTRALIZED),
        ("node_2", 70.0, -0.4, ControlMode.DECENTRALIZED),
        ("node_3", 50.0, 0.8, ControlMode.DECENTRALIZED),
        ("node_4", 30.0, -0.7, ControlMode.DECENTRALIZED),
        ("node_5", 90.0, 0.1, ControlMode.EMERGENCE),
        ("node_6", 20.0, -0.2, ControlMode.STIGMERGIC),
        ("node_7", 10.0, 0.5, ControlMode.STIGMERGIC), # starving
        ("node_8", 15.0, -0.9, ControlMode.STIGMERGIC), # starving
        ("node_9", 60.0, 0.3, ControlMode.HIERARCHICAL),
        ("node_10", 40.0, -0.1, ControlMode.HIERARCHICAL),
        ("food", 100.0, 0.0, ControlMode.EMERGENCE)
    ]
    
    for nid, energy, op, mode in nodes_data:
        node = EmergenceNode(
            id=nid,
            opinions={"main": op},
            resources={"energy": energy},
            control_mode=mode
        )
        swarm.graph.add_node(node)

    # 2. Add edges connecting them (Trophallaxis, Command, Stigmergy, etc.)
    edges_data = [
        ("nest", "node_1", TrophallaxisEdge),
        ("nest", "node_2", TrophallaxisEdge),
        ("node_1", "node_3", TrophallaxisEdge),
        ("node_2", "node_4", TrophallaxisEdge),
        ("node_3", "node_7", TrophallaxisEdge), # feed starving
        ("node_4", "node_8", TrophallaxisEdge), # feed starving
        
        ("nest", "node_5", EmergenceEdge),
        ("node_5", "node_6", EmergenceEdge),
        ("node_6", "food", EmergenceEdge),
        
        ("node_9", "node_10", AdaptiveEdge, EdgeType.COMMAND),
        ("node_9", "node_1", AdaptiveEdge, EdgeType.COMMAND),
        ("node_10", "node_2", AdaptiveEdge, EdgeType.COMMAND)
    ]
    
    for edge_info in edges_data:
        src, tgt = edge_info[0], edge_info[1]
        edge_cls = edge_info[2]
        
        if len(edge_info) == 4:
            etype = edge_info[3]
            edge = edge_cls(source_id=src, target_id=tgt, weight=1.0, edge_type=etype)
        else:
            edge = edge_cls(source_id=src, target_id=tgt, weight=1.0)
            
        swarm.graph.add_edge(edge)

initialize_visualization_swarm()

class SwarmHTTPHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        # Silence standard HTTP logging to keep console clean
        pass

    def send_json(self, data: Any, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, cls=SwarmStateEncoder).encode("utf-8"))

    def send_html(self, file_path: str) -> None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        except Exception as e:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(f"File not found: {str(e)}".encode("utf-8"))

    def do_GET(self) -> None:
        if self.path == "/" or self.path == "/index.html":
            # Find static index.html path
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            html_path = os.path.join(curr_dir, "resources", "index.html")
            self.send_html(html_path)
            
        elif self.path == "/api/state":
            self.send_json(self._get_swarm_state_payload())
            
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        
        try:
            body = json.loads(post_data) if post_data else {}
        except Exception:
            body = {}

        if self.path == "/api/step":
            steps = body.get("steps", 1)
            for _ in range(steps):
                swarm.hybrid_step()
            self.send_json(self._get_swarm_state_payload())
            
        elif self.path == "/api/mode":
            mode_val = body.get("mode")
            node_id = body.get("node_id")
            
            if mode_val in ControlMode.__members__:
                cm = ControlMode(mode_val)
                if node_id:
                    swarm.set_control_mode({node_id: cm})
                else:
                    swarm.set_control_mode(cm)
            self.send_json(self._get_swarm_state_payload())
            
        elif self.path == "/api/checkpoint":
            ckpt = swarm.checkpoint()
            checkpoints[ckpt.checkpoint_id] = ckpt
            self.send_json({
                "status": "success",
                "checkpoint_id": ckpt.checkpoint_id,
                "timestamp": ckpt.timestamp,
                "state_hash": ckpt.state_hash
            })
            
        elif self.path == "/api/restore":
            ckpt_id = body.get("checkpoint_id")
            if ckpt_id in checkpoints:
                swarm.restore(checkpoints[ckpt_id])
                self.send_json(self._get_swarm_state_payload())
            else:
                self.send_json({"error": f"Checkpoint ID {ckpt_id} not found"}, 400)
                
        else:
            self.send_response(404)
            self.end_headers()

    def _get_swarm_state_payload(self) -> Dict[str, Any]:
        """Assembles state variables for visualization payload."""
        # 1. Compile nodes info
        nodes = []
        for nid, node in swarm.graph.nodes.items():
            if isinstance(node, EmergenceNode):
                nodes.append({
                    "id": str(node.id),
                    "energy": node.resources.get("energy", 100.0),
                    "opinion": node.opinions.get("main", 0.0),
                    "mode": node.control_mode.value,
                    "starving": node.local_memory.get("starving", False)
                })
            else:
                nodes.append({
                    "id": str(node.id),
                    "energy": 50.0,
                    "opinion": 0.0,
                    "mode": "BASE",
                    "starving": False
                })

        # 2. Compile edges info
        edges = []
        for edge in swarm.graph.edges.values():
            edges.append({
                "id": edge.id,
                "source": edge.source_id,
                "target": edge.target_id,
                "weight": edge.weight,
                "strength": edge.strength,
                "type": edge.edge_type.value,
                "usage": edge.usage_count
            })

        # 3. Health status
        health = swarm.compute_swarm_health()
        
        # 4. Logs
        logs = []
        for rec in swarm.provenance.chain[-15:]:
            logs.append({
                "index": rec.index,
                "actor": rec.delta.actor,
                "op": rec.delta.operation,
                "target": rec.delta.target,
                "hash": rec.current_hash[:12]
            })

        # 5. Checkpoints
        ckpt_list = [
            {"id": cid, "time": ck.timestamp, "hash": ck.state_hash[:12]}
            for cid, ck in checkpoints.items()
        ]

        return {
            "name": swarm.name,
            "step": swarm.step_index,
            "nodes": nodes,
            "edges": edges,
            "health": health.model_dump(),
            "logs": logs,
            "checkpoints": ckpt_list
        }

def start_server(port: int = 8000, open_browser: bool = True) -> None:
    """Spawns the local visualizer server."""
    handler = SwarmHTTPHandler
    # Enable socket reuse to prevent port binding blockages on quick restarts
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print("=" * 80)
        print(f" BASE GRAPH WEB VISUALIZATION SERVER RUNNING")
        print(f" URL: http://localhost:{port}/")
        print("=" * 80)
        
        if open_browser:
            webbrowser.open(f"http://localhost:{port}/")
            
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down visualization server.")
            sys.exit(0)

if __name__ == "__main__":
    start_server()
