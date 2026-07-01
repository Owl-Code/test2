import os
import sys
import time
import subprocess
import traceback
import urllib.request
import urllib.parse
import json
import re
from typing import Dict, Any, Optional, List
from base_graph.primitives.edge import AdaptiveEdge
from base_graph.types import EdgeType
from graph_swarm_harness.tools.registry import ToolRegistry
from graph_swarm_harness.core.emergence import calculate_swarm_emergence

def _check_path_safety(path: str, workspace_root: str) -> str:
    """Ensures paths are resolved within the workspace root to prevent directory traversal."""
    abs_root = os.path.abspath(workspace_root)
    # Handle relative paths resolved from root
    if not os.path.isabs(path):
        resolved_path = os.path.abspath(os.path.join(abs_root, path))
    else:
        resolved_path = os.path.abspath(path)
        
    if not resolved_path.startswith(abs_root):
        raise PermissionError(f"Path access violation: {path} is outside workspace root {workspace_root}")
    return resolved_path

# --- Tool Callables ---

def read_file_tool(path: str, run_context: Dict[str, Any]) -> str:
    workspace = run_context.get("workspace_root", ".")
    safe_path = _check_path_safety(path, workspace)
    if not os.path.exists(safe_path):
        return f"Error: File not found at {path}"
    with open(safe_path, "r", encoding="utf-8") as f:
        return f.read()

def write_file_tool(path: str, content: str, run_context: Dict[str, Any]) -> str:
    workspace = run_context.get("workspace_root", ".")
    safe_path = _check_path_safety(path, workspace)
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully wrote {len(content)} characters to {path}"

def list_dir_tool(path: str = ".", run_context: Dict[str, Any] = None) -> str:
    run_context = run_context or {}
    workspace = run_context.get("workspace_root", ".")
    safe_path = _check_path_safety(path, workspace)
    if not os.path.exists(safe_path):
        return f"Error: Directory not found at {path}"
    if not os.path.isdir(safe_path):
        return f"Error: {path} is not a directory"
    
    entries = os.listdir(safe_path)
    result = []
    for entry in entries:
        full_path = os.path.join(safe_path, entry)
        if os.path.isdir(full_path):
            result.append(f"[DIR]  {entry}")
        else:
            result.append(f"[FILE] {entry} ({os.path.getsize(full_path)} bytes)")
    return "\n".join(result) if result else "(Empty directory)"

def execute_python_snippet_tool(code: str, run_context: Dict[str, Any]) -> str:
    """Executes python code in a separate subprocess for safety & process isolation."""
    # We can write the code to a temp file or run it via python -c. 
    # Let's write it to a temporary file inside the workspace for clean traceback formatting.
    workspace = run_context.get("workspace_root", ".")
    temp_dir = os.path.join(workspace, ".swarm_temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_file = os.path.join(temp_dir, f"snippet_{os.getpid()}.py")
    
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)
        
        # Run subprocess with timeout
        res = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = f"Exit Code: {res.returncode}\n"
        if res.stdout:
            output += f"Stdout:\n{res.stdout}\n"
        if res.stderr:
            output += f"Stderr:\n{res.stderr}\n"
        return output
    except subprocess.TimeoutExpired:
        return "Error: Execution timed out after 10 seconds."
    except Exception as e:
        return f"Error executing snippet: {str(e)}\n{traceback.format_exc()}"
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass

def update_swarm_node_state_tool(node_id: str, updates: Dict[str, Any], run_context: Dict[str, Any]) -> str:
    swarm = run_context["swarm"]
    agent = swarm.get_agent(node_id)
    if not agent:
        return f"Error: Agent node {node_id} not found."
    
    before = agent.node.state.copy()
    for k, v in updates.items():
        if k in ("role", "active_skills", "available_tools"):
            setattr(agent, k, v)
        else:
            agent.node.state[k] = v
            
    swarm.provenance.add_mutation(
        actor=run_context.get("agent_id", "system"),
        operation="update_swarm_node_state",
        target=node_id,
        before=before,
        after=agent.node.state.copy()
    )
    return f"Successfully updated state of agent {node_id}"

def query_swarm_emergence_tool(run_context: Dict[str, Any]) -> str:
    swarm = run_context["swarm"]
    emergence = calculate_swarm_emergence(swarm)
    agents = swarm.get_agents()
    agent_reports = []
    for a in agents:
        agent_reports.append(f"  - {a.id} ({a.role}): energy={a.energy:.1f}, emergence_contribution={a.emergence_level:.2f}")
    
    return (
        f"Global Swarm Emergence Level: {emergence:.4f}\n"
        f"Active Agents:\n" + "\n".join(agent_reports)
    )

def create_handoff_edge_tool(target_agent_id: str, message: str, run_context: Dict[str, Any]) -> str:
    swarm = run_context["swarm"]
    sender_id = run_context["agent_id"]
    
    target_agent = swarm.get_agent(target_agent_id)
    if not target_agent:
        return f"Error: Target agent {target_agent_id} not found."
        
    # Append message to target's inbox
    target_agent.receive_message(sender_id=sender_id, message=message)
    
    # Log intra-swarm message
    sender_agent = swarm.get_agent(sender_id)
    sender_role = sender_agent.role if sender_agent else "agent"
    target_role = target_agent.role if target_agent else "agent"
    
    if not hasattr(swarm, "intra_swarm_messages"):
        swarm.intra_swarm_messages = []
        
    swarm.intra_swarm_messages.append({
        "sender": f"{sender_id} ({sender_role})",
        "target": f"{target_agent_id} ({target_role})",
        "text": message,
        "timestamp": int(time.time())
    })
    
    # Create or update communication/handoff edge
    edge_id = f"{sender_id}->{target_agent_id}"
    edge = swarm.graph.edges.get(edge_id)
    if not edge:
        edge = AdaptiveEdge(source_id=sender_id, target_id=target_agent_id, edge_type=EdgeType.COMMUNICATION)
        swarm.graph.add_edge(edge)
        
    edge.update_weight(0.1, reason=f"Handoff from {sender_id} to {target_agent_id}")
    
    swarm.provenance.add_mutation(
        actor=sender_id,
        operation="create_handoff_edge",
        target=target_agent_id,
        before=None,
        after={"message": message}
    )
    return f"Successfully sent handoff message to {target_agent_id}"

def diffuse_signal_tool(signal: str, intensity: float, steps: int = 3, run_context: Dict[str, Any] = None) -> str:
    run_context = run_context or {}
    swarm = run_context["swarm"]
    agent_id = run_context["agent_id"]
    
    # Stigmergically spread a signal to neighbors
    agent = swarm.get_agent(agent_id)
    if agent:
        agent.node.deposit_stigmergy(signal, intensity)
        
    # Run the base graph's diffusion steps on the diffusion subgraph if nodes are available
    swarm.diffusion_subgraph.run_diffusion(model="opinion", steps=steps)
    
    return f"Successfully diffused signal '{signal}' with intensity {intensity} across {steps} steps."

def web_search_tool(query: str, run_context: Dict[str, Any] = None) -> str:
    """Queries DuckDuckGo HTML search for snippets matching the query."""
    print(f"[Tool] Querying web search: '{query}'")
    try:
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode("utf-8", errors="ignore")
            
        results = []
        # Find result articles in DDG HTML layout
        snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        urls = re.findall(r'<a class="result__url"[^>]*>(.*?)</a>', html, re.DOTALL)
        
        for i in range(min(5, len(snippets))):
            clean_title = re.sub(r'<[^>]+>', '', urls[i]).strip() if i < len(urls) else "Result"
            clean_snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
            results.append(f"[{i+1}] {clean_title}\nSnippet: {clean_snippet}")
            
        if not results:
            # Fallback to duckduckgo instant answer JSON api
            url_json = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1"
            req_json = urllib.request.Request(url_json, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_json, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            abstract = data.get("AbstractText", "")
            if abstract:
                return f"Abstract: {abstract}"
            return "No web results found."
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Error executing web search: {str(e)}"

def fetch_webpage_content_tool(url: str, run_context: Dict[str, Any] = None) -> str:
    """Downloads webpage HTML, strips script/style tags, and returns plain text."""
    print(f"[Tool] Fetching webpage content: {url}")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            html = response.read().decode("utf-8", errors="ignore")
            
        # Clean HTML: remove script, style, head, and comments
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<head[^>]*>.*?</head>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        
        # Replace common tags with spaces/newlines
        html = re.sub(r'<p[^>]*>', '\n\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<br[^>]*>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<li[^>]*>', '\n- ', html, flags=re.IGNORECASE)
        
        # Remove remaining tags
        text = re.sub(r'<[^>]+>', '', html)
        
        # Collapse multiple spaces and empty lines
        lines = [line.strip() for line in text.split('\n')]
        non_empty = [line for line in lines if line]
        clean_text = '\n'.join(non_empty)
        
        # Cap text size to prevent token overflow
        if len(clean_text) > 8000:
            return clean_text[:8000] + "\n\n... (content truncated to 8000 characters) ..."
        return clean_text
    except Exception as e:
        return f"Error fetching webpage: {str(e)}"

# --- Setup Helper ---

def setup_core_tools(registry: ToolRegistry):
    """Registers all core tools to the provided ToolRegistry."""
    registry.register_tool(
        name="read_file",
        description="Reads the text contents of a file in the workspace.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file relative to the workspace root."}
            },
            "required": ["path"]
        },
        func=read_file_tool,
        risk_level="LOW"
    )
    
    registry.register_tool(
        name="write_file",
        description="Writes content to a file in the workspace (creates directories if needed).",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The target file path relative to the workspace root."},
                "content": {"type": "string", "description": "The text content to write."}
            },
            "required": ["path", "content"]
        },
        func=write_file_tool,
        risk_level="HIGH"
    )
    
    registry.register_tool(
        name="list_dir",
        description="Lists the files and subdirectories in a workspace path.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The directory path to list (default: root)."}
            }
        },
        func=list_dir_tool,
        risk_level="LOW"
    )
    
    registry.register_tool(
        name="execute_python_snippet",
        description="Executes a Python code block and returns its standard output/error. Run isolated in a subprocess.",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The complete Python script block to execute."}
            },
            "required": ["code"]
        },
        func=execute_python_snippet_tool,
        risk_level="HIGH"
    )
    
    registry.register_tool(
        name="update_swarm_node_state",
        description="Directly updates attributes or state dict keys of an agent node in the swarm.",
        parameters={
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "The ID of the agent node to modify."},
                "updates": {
                    "type": "object", 
                    "description": "Dictionary of keys and values to update (e.g. role, active_skills, etc.)."
                }
            },
            "required": ["node_id", "updates"]
        },
        func=update_swarm_node_state_tool,
        risk_level="MEDIUM"
    )
    
    registry.register_tool(
        name="query_swarm_emergence",
        description="Queries the current global and local emergence metrics of the swarm graph.",
        parameters={
            "type": "object",
            "properties": {}
        },
        func=query_swarm_emergence_tool,
        risk_level="LOW"
    )
    
    registry.register_tool(
        name="create_handoff_edge",
        description="Sends a text message to another agent's inbox, creating or reinforcing a communication edge.",
        parameters={
            "type": "object",
            "properties": {
                "target_agent_id": {"type": "string", "description": "The ID of the target recipient agent."},
                "message": {"type": "string", "description": "The content of the handoff message."}
            },
            "required": ["target_agent_id", "message"]
        },
        func=create_handoff_edge_tool,
        risk_level="LOW"
    )
    
    registry.register_tool(
        name="diffuse_signal",
        description="Deposits a stigmergic pheromone signal on the local node and diffuses signals across the graph.",
        parameters={
            "type": "object",
            "properties": {
                "signal": {"type": "string", "description": "The name of the pheromone signal."},
                "intensity": {"type": "number", "description": "The signal strength to deposit (e.g. 0.0 to 10.0)."},
                "steps": {"type": "integer", "description": "Number of diffusion hops."}
            },
            "required": ["signal", "intensity"]
        },
        func=diffuse_signal_tool,
        risk_level="LOW"
    )
    
    registry.register_tool(
        name="web_search",
        description="Queries the web for search snippets matching the query.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query query term."}
            },
            "required": ["query"]
        },
        func=web_search_tool,
        risk_level="LOW"
    )
    
    registry.register_tool(
        name="fetch_webpage",
        description="Downloads the contents of a webpage, strips HTML, and returns raw plain text.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The absolute HTTP/HTTPS URL to fetch."}
            },
            "required": ["url"]
        },
        func=fetch_webpage_content_tool,
        risk_level="LOW"
    )
    
    registry.register_tool(
        name="reply_to_operator",
        description="Sends a direct text message reply back to the human operator chat window.",
        parameters={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The message response content."}
            },
            "required": ["message"]
        },
        func=reply_to_operator_tool,
        risk_level="LOW"
    )
    
    registry.register_tool(
        name="create_new_role",
        description="Creates a new agent role template configuration dynamically, defining its skills, tools, and persona instructions.",
        parameters={
            "type": "object",
            "properties": {
                "role_name": {"type": "string", "description": "The name of the new role template to create (e.g. doc_writer)."},
                "skills": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "List of active skills (e.g. ['file_io'])."
                },
                "tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of available tools (e.g. ['write_file'])."
                },
                "persona": {"type": "string", "description": "The system persona prompt defining the agent's behavior."}
            },
            "required": ["role_name", "skills", "tools", "persona"]
        },
        func=create_new_role_tool,
        risk_level="HIGH"
    )

def reply_to_operator_tool(message: str, run_context: Dict[str, Any]) -> str:
    """Sends a text message back to the human operator chat console."""
    swarm = run_context["swarm"]
    agent_id = run_context["agent_id"]
    agent = swarm.get_agent(agent_id)
    role = agent.role if agent else "agent"
    
    # Store replies in the swarm graph state metadata (which persists)
    swarm.chat_replies.append({
        "sender": f"{agent_id} ({role})",
        "text": message,
        "timestamp": int(time.time())
    })
    
    # Log mutation into provenance
    swarm.provenance.add_mutation(
        actor=agent_id,
        operation="reply_to_operator",
        target="operator",
        before=None,
        after={"message": message}
    )
    return "Reply successfully registered for the operator."

def create_new_role_tool(
    role_name: str, 
    skills: List[str], 
    tools: List[str], 
    persona: str, 
    run_context: Dict[str, Any]
) -> str:
    """Creates a new role template configuration in the swarm dynamically."""
    swarm = run_context["swarm"]
    actor = run_context.get("agent_id", "operator")
    
    role_name = role_name.strip().lower()
    before = swarm.role_templates.get(role_name)
    
    # Update active role templates
    swarm.role_templates[role_name] = {
        "skills": list(skills),
        "tools": list(tools),
        "persona": persona.strip()
    }
    
    # Log mutation to audit provenance trail
    swarm.provenance.add_mutation(
        actor=actor,
        operation="create_role_template",
        target=role_name,
        before=before,
        after=swarm.role_templates[role_name].copy()
    )
    return f"Role template '{role_name}' successfully created/updated."
