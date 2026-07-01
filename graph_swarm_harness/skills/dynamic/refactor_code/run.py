import os
import json
import urllib.request
from graph_swarm_harness.tools.core_tool_implementations import _check_path_safety

path = args.get("path")
instructions = args.get("instructions")
run_context = run_context or {}
workspace = run_context.get("workspace_root", ".")

try:
    # 1. Resolve safe path in workspace
    safe_path = _check_path_safety(path, workspace)
    if not os.path.exists(safe_path):
        result = f"Error: Target file not found at {path}"
    else:
        # 2. Read existing content
        with open(safe_path, "r", encoding="utf-8") as f:
            code_content = f.read()

        # 3. Call local Ollama generation API
        prompt = (
            f"You are an expert Python software refactoring assistant.\n"
            f"Refactor the following Python code according to these instructions: \"{instructions}\".\n\n"
            f"Respond ONLY with the complete, functional, refactored Python code. Do NOT include markdown code block formatting (like ```python or ```), explanation text, or preambles. Output only raw, compilable Python code.\n\n"
            f"Code to refactor:\n"
            f"{code_content}"
        )
        
        payload = {
            "model": "qwen2.5:3b-instruct",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }
        
        url = "http://localhost:11434/api/generate"
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            
        refactored_code = resp_data.get("response", "").strip()
        
        # Clean any accidental markdown wrapper tags if returned
        if refactored_code.startswith("```python"):
            refactored_code = refactored_code[9:]
        elif refactored_code.startswith("```"):
            refactored_code = refactored_code[3:]
        if refactored_code.endswith("```"):
            refactored_code = refactored_code[:-3]
        refactored_code = refactored_code.strip()
        
        # 4. Save refactored code back to workspace file
        if refactored_code:
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(refactored_code)
            result = f"Successfully refactored {path} based on instructions: '{instructions}'"
        else:
            result = "Error: Local LLM returned an empty response."
except Exception as e:
    result = f"Error running refactor_code dynamic skill: {str(e)}"
