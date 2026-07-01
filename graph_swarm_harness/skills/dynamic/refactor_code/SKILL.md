---
name: refactor_code
description: "Loads a target python script, refactors it using the local LLM based on instructions, and saves it back."
when_to_use: "When a reviewer or operator flags issues with code cleanliness, docstrings, performance, or structural bugs."
input_schema:
  type: object
  properties:
    path:
      type: string
      description: "The path of the Python file relative to the workspace root."
    instructions:
      type: string
      description: "Instructions on what to improve, e.g. 'add docstrings', 'optimize performance', 'fix edge cases'."
  required: [path, instructions]
risk_level: HIGH
---
# Refactor Code Dynamic Skill
Uses local Ollama inference to modify files on disk in place.
