import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional

class ToolsRegistry:
    """Discover and register tools from the agent.functions.tools package.

    Behavior:
    - Always uses the `agent/functions/tools` folder inside the repo.
    - Scans that folder for modules matching `*_tool.py`.
    - Imports each module and instantiates any classes that subclass `BaseTool`.

    Registered tools are accessible via `get`, `register`, and `list_tools`.
    """

    def __init__(self):
        self.tools_package = "agent.functions.tools"
        tool_directory = Path(__file__).resolve().parent / "tools"
        self.tools_path = tool_directory
        self.tools: Dict[str, Any] = {}
        self.discover_and_register()

    def register(self, name: str, tool: Any) -> None:
        self.tools[name] = tool

    def get(self, name: str) -> Optional[Any]:
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def discover_and_register(self) -> None:
        pkg = importlib.import_module(self.tools_package)

        for name in getattr(pkg, "__all__", []):
            obj = getattr(pkg, name)
            instance = obj() 
            self.register(instance.name, instance)
    
    def as_function_schemas(self) -> List[Dict[str, Any]]:
        return [tool.generate_schema() for tool in self.tools.values()]