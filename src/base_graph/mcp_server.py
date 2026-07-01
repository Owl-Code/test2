import sys
import json
import traceback
from typing import Any, Dict, List
from base_graph import HybridControlSwarmGraph, EmergenceNode, ControlMode, Action, Decision

# Global swarm instance for MCP session state
swarm = HybridControlSwarmGraph(name="mcp-swarm")

# Setup dummy nodes for initial state
for i in range(10):
    node = EmergenceNode(
        id=f"node_{i}",
        opinions={"main": 0.0},
        resources={"energy": 100.0},
        control_mode=ControlMode.EMERGENCE
    )
    swarm.graph.add_node(node)

def list_tools() -> List[Dict[str, Any]]:
    """List of tools exposed by the MCP server."""
    return [
        {
            "name": "get_swarm_status",
            "description": "Returns the current SwarmHealthReport containing emergence levels, entropy, and blockchain integrity.",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "step_swarm",
            "description": "Runs a specified number of simulation steps on the swarm graph.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "steps": {"type": "integer", "description": "Number of steps to run.", "default": 1}
                }
            }
        },
        {
            "name": "inject_override",
            "description": "Applies a absolute human override action to a specific node, bypassing local heuristics.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "Target Node UUID/String."},
                    "action_type": {"type": "string", "description": "e.g. SHARE_RESOURCE, IDLE."},
                    "parameters": {"type": "object", "description": "JSON dictionary of parameters for the action."}
                },
                "required": ["node_id", "action_type"]
            }
        },
        {
            "name": "get_provenance_logs",
            "description": "Retrieves the blockchain audit history of all state changes.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Limit log count.", "default": 10}
                }
            }
        },
        {
            "name": "restore_checkpoint",
            "description": "Rolls back the swarm state to a serialized checkpoint string.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "checkpoint_json": {"type": "string", "description": "Full JSON string of checkpoint."}
                },
                "required": ["checkpoint_json"]
            }
        }
    ]

def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Routes and executes tool calls."""
    if name == "get_swarm_status":
        health = swarm.compute_swarm_health()
        mcp_packet = swarm.provenance.export_mcp_packet()
        result = {
            "health_report": health.model_dump(),
            "mcp_provenance_header": mcp_packet
        }
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
        
    elif name == "step_swarm":
        steps = arguments.get("steps", 1)
        results = []
        for _ in range(steps):
            res = swarm.hybrid_step()
            results.append({
                "step": res.step_index,
                "modes": res.active_modes,
                "hash": res.provenance_hash
            })
        return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}
        
    elif name == "inject_override":
        node_id = arguments["node_id"]
        action_type = arguments["action_type"]
        parameters = arguments.get("parameters", {})
        
        node = swarm.graph.nodes.get(node_id)
        if not node:
            return {"isError": True, "content": [{"type": "text", "text": f"Node {node_id} not found."}]}
            
        # Standard human override integration
        action = Action(action_type=action_type, parameters=parameters)
        decision = Decision(
            node_id=node_id,
            selected_action=action,
            confidence=1.0,
            reason="HUMAN OVERRIDE INJECTED VIA MCP"
        )
        
        # Enforce action directly onto node memory
        if isinstance(node, EmergenceNode):
            node.local_memory["human_override"] = decision.model_dump()
            # Direct application
            if action_type == "SHARE_RESOURCE":
                target = parameters.get("target_id")
                amount = parameters.get("amount", 10.0)
                if target and target in swarm.graph.nodes:
                    node.resources["energy"] = max(0.0, node.resources.get("energy", 0.0) - amount)
                    swarm.graph.nodes[target].resources["energy"] = swarm.graph.nodes[target].resources.get("energy", 0.0) + amount
            
            swarm.provenance.add_mutation(
                actor="mcp_human_operator",
                operation="inject_human_override",
                target=node_id,
                before=None,
                after=decision.model_dump(),
                meta={"action": action_type}
            )
            
        return {"content": [{"type": "text", "text": f"Successfully injected human override command to {node_id}."}]}
        
    elif name == "get_provenance_logs":
        limit = arguments.get("limit", 10)
        records = [r.model_dump() for r in swarm.provenance.chain[-limit:]]
        return {"content": [{"type": "text", "text": json.dumps(records, indent=2)}]}
        
    elif name == "restore_checkpoint":
        ckpt_str = arguments["checkpoint_json"]
        try:
            swarm.restore(ckpt_str)
            return {"content": [{"type": "text", "text": "Swarm state restored successfully to checkpoint. Hash matches."}]}
        except Exception as e:
            return {"isError": True, "content": [{"type": "text", "text": f"Failed to restore checkpoint: {str(e)}"}]}
            
    else:
        raise ValueError(f"Unknown tool: {name}")

def handle_jsonrpc(line: str) -> str:
    """Processes stdio JSON-RPC request and returns JSON-RPC response."""
    try:
        req = json.loads(line)
    except Exception:
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})

    if req.get("jsonrpc") != "2.0":
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": req.get("id")})

    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params", {})

    try:
        # Standard MCP protocol routing
        if method == "initialize":
            return json.dumps({
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "base-graph-mcp", "version": "1.0.0"}
                },
                "id": req_id
            })
            
        elif method == "tools/list":
            return json.dumps({
                "jsonrpc": "2.0",
                "result": {"tools": list_tools()},
                "id": req_id
            })
            
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})
            res = call_tool(name, args)
            return json.dumps({
                "jsonrpc": "2.0",
                "result": res,
                "id": req_id
            })
            
        elif method == "ping":
            return json.dumps({"jsonrpc": "2.0", "result": {}, "id": req_id})
            
        else:
            return json.dumps({
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": req_id
            })
    except Exception as e:
        return json.dumps({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e), "data": traceback.format_exc()},
            "id": req_id
        })

def main():
    """Main input loop for reading stdin and responding via stdout."""
    # Ensure stdout is unbuffered and flush immediately
    sys.stdout.reconfigure(encoding="utf-8") # type: ignore
    
    # Check if we are run in interactive terminal mode instead of stdio pipeline
    if sys.stdin.isatty():
        print("Base Graph MCP Server running in mock interactive CLI mode.")
        print("Send JSON-RPC queries like: {'jsonrpc': '2.0', 'method': 'tools/list', 'id': 1}")
        print("Type 'exit' to quit.\n")
        
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line_str = line.strip()
            if line_str == "exit":
                break
            if not line_str:
                continue
                
            response = handle_jsonrpc(line_str)
            print(response)
            sys.stdout.flush()
        except KeyboardInterrupt:
            break
        except Exception as e:
            sys.stderr.write(f"Error: {str(e)}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
