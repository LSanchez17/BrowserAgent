from typing import Any, Dict, Optional

class BaseTool:
    name: str
    description: str

    def __init__(self, name: Optional[str] = None, description: str = ""):
        self.name = name or self.__class__.__name__
        self.description = description

    def execute(self, *args, **kwargs):
        raise NotImplementedError("Tools must implement `execute` to perform their action")
    
    def parameters(self) -> Dict[str, Any]:
        raise NotImplementedError("Tools must implement `parameters` to specify their input schema")
    
    def generate_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters(),
            },
        }
    
    def __repr__(self):
        return f"<Tool name={self.name} description={self.description}>"
