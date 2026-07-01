from typing import Dict, Any, Callable, List, Optional

class Tool:
    """Represents a low-level atomic capability that can be invoked by agents."""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any], func: Callable, risk_level: str = "LOW"):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func
        self.risk_level = risk_level

    def to_ollama_format(self) -> Dict[str, Any]:
        """Converts the tool description to Ollama's tool definition format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def execute(self, *args, **kwargs) -> Any:
        """Executes the tool's underlying callable with parameters."""
        return self.func(*args, **kwargs)

class ToolRegistry:
    """Registry to manage and look up available tools."""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], func: Callable, risk_level: str = "LOW"):
        self.tools[name] = Tool(name, description, parameters, func, risk_level)

    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self.tools.values())
