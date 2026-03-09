"""Simple wrapper around Ollama async client for predictable outputs.

This provides a small interface to generate from the configured model and
attempt JSON parsing when a schema is provided.
"""
from typing import Any, Dict, Optional
import json
import ollama
import asyncio

from .functions.tool_registry import ToolsRegistry


class LLMClient:
    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen3.5:9b"):
        self.host = host
        self.model = model
        self.tools_schemas = ToolsRegistry().as_function_schemas()
        self.tools = ToolsRegistry().tools
        self.client = ollama.AsyncClient(host=host)

    async def evaluate(self, prompt: str, schema: Dict[str, Any], timeout: Optional[int] = None) -> Any:
        """Evaluate the incoming prompt. Schema is required and will be used to structure the response

        Returns parsed Python object when schema is present, otherwise raw text.
        """
        try:
            print(f"\n🧠 Asking LLM...")
            response = await self.client.generate(model=self.model, prompt=prompt, stream=False, format=schema)
            answer = response.get('response')
            
            return json.loads(answer)
        except Exception as e:
            raise e

    async def chat(self, messages: list):
        """Call Ollama chat API with tools if available.

        Returns the raw response from the Ollama client. This wrapper will use
        the async client's `chat` if present, otherwise fall back to running
        the sync `ollama.chat` in a thread.
        """
        try:
            print(f"\n🧠 Asking LLM (chat)...")
            if hasattr(self.client, "chat"):
                resp = await self.client.chat(model=self.model, messages=messages, tools=self.tools_schemas)
                return resp

            # Fallback to synchronous call in a thread
            def _sync_call():
                return ollama.chat(model=self.model, messages=messages, tools=self.tools_schemas, think=True)

            resp = await asyncio.to_thread(_sync_call)
            return resp
        except Exception as e:
            raise

    async def execute_tool_call(self, call, page):
        """Execute a registered tool by name with the provided arguments."""
        tool_name = getattr(call.function, 'name')
        tool_args = getattr(call.function, 'arguments', {})
        print(f"\n🔧 Executing tool: {tool_name} with args: {tool_args}")

        # Verify tool exists in registry
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found in registry.")

        # Default `requires_page` to True when a page object is provided
        if page is not None:
            tool_args.setdefault("requires_page", True)

        # Execute the tool
        tool_callable = self.tools[tool_name].execute
        result = tool_callable(**tool_args)
        
        # If the result is a coroutine (async), await it before returning
        if asyncio.iscoroutine(result):
            result = await result

        return tool_name, result
