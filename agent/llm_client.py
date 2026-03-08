"""Simple wrapper around Ollama async client for predictable outputs.

This provides a small interface to generate from the configured model and
attempt JSON parsing when a schema is provided.
"""
from typing import Any, Dict, Optional
import json
import ollama


class LLMClient:
    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen3:8b"):
        self.host = host
        self.model = model
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
