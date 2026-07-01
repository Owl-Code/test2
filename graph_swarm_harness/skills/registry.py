from typing import Dict, Any, Callable, List, Optional

class Skill:
    """Represents a high-level task/capability that can be invoked by agents.
    
    Skills can orchestrate multiple tool calls, external subprocesses, or state changes.
    """
    
    def __init__(self, name: str, description: str, when_to_use: str, input_schema: Dict[str, Any], func: Callable, risk_level: str = "LOW"):
        self.name = name
        self.description = description
        self.when_to_use = when_to_use
        self.input_schema = input_schema
        self.func = func
        self.risk_level = risk_level

    def to_ollama_format(self) -> Dict[str, Any]:
        """Formats the skill as an Ollama function specification so the LLM knows how to call it."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": f"When to use: {self.when_to_use}. {self.description}",
                "parameters": self.input_schema
            }
        }

    def execute(self, *args, **kwargs) -> Any:
        return self.func(*args, **kwargs)

class SkillRegistry:
    """Registry to register and look up available agent skills."""
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}

    def register_skill(self, name: str, description: str, when_to_use: str, input_schema: Dict[str, Any], func: Callable, risk_level: str = "LOW"):
        self.skills[name] = Skill(name, description, when_to_use, input_schema, func, risk_level)

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self.skills.values())

    def load_skills_from_directory(self, directory: str) -> None:
        """Loads and registers markdown frontmatter skills dynamically from subdirectories."""
        import os
        import yaml
        if not os.path.exists(directory):
            return
            
        for folder in os.listdir(directory):
            folder_path = os.path.join(directory, folder)
            if not os.path.isdir(folder_path):
                continue
                
            skill_file = os.path.join(folder_path, "SKILL.md")
            run_file = os.path.join(folder_path, "run.py")
            
            if os.path.exists(skill_file):
                try:
                    with open(skill_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Split frontmatter between --- blocks
                    parts = content.split("---")
                    if len(parts) >= 3:
                        meta = yaml.safe_load(parts[1]) or {}
                        
                        name = meta.get("name", folder)
                        desc = meta.get("description", "")
                        when = meta.get("when_to_use", "")
                        schema = meta.get("input_schema", {"type": "object", "properties": {}})
                        risk = meta.get("risk_level", "LOW")
                        
                        # Determine execution function
                        if os.path.exists(run_file):
                            def make_executor(script_path):
                                def dynamic_executor(*args, **kwargs):
                                    with open(script_path, "r", encoding="utf-8") as sf:
                                        script_code = sf.read()
                                    # Create execution context
                                    locs = {"args": kwargs, "run_context": kwargs.get("run_context") or (args[0] if args else {})}
                                    exec(script_code, globals(), locs)
                                    return locs.get("result", "Dynamic skill executed successfully.")
                                return dynamic_executor
                            
                            executor = make_executor(run_file)
                        else:
                            executor = lambda *args, **kwargs: "Dynamic skill execution stub. Script not found."
                            
                        self.register_skill(
                            name=name,
                            description=desc,
                            when_to_use=when,
                            input_schema=schema,
                            func=executor,
                            risk_level=risk
                        )
                        print(f"[SkillRegistry] Dynamically loaded skill '{name}' from {folder_path}")
                except Exception as e:
                    print(f"[SkillRegistry] Error loading dynamic skill from {folder_path}: {e}")
