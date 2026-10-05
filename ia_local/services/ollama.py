import os
import requests

from .proveedor import AIProvider


class OllamaError(RuntimeError):
    pass


class OllamaProvider(AIProvider):
    def __init__(self):
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        self.model = os.environ.get(
            "OLLAMA_MODEL",
            "qwen3:4b-instruct-2507-q4_K_M",
        )
        self.timeout = int(os.environ.get("OLLAMA_TIMEOUT", "90"))

    def healthcheck(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.ok
        except requests.RequestException:
            return False

    def model_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get("models", [])
            names = {item.get("name") for item in models}
            return self.model in names
        except (requests.RequestException, ValueError):
            return False

    def structured_chat(self, messages, schema) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": schema,
            "options": {
                "temperature": 0,
                "num_predict": 600,
            },
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise OllamaError(f"No fue posible consultar Ollama: {exc}") from exc
        except ValueError as exc:
            raise OllamaError("Ollama devolvió una respuesta HTTP que no es JSON.") from exc

        content = (data.get("message") or {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise OllamaError("Ollama no devolvió contenido en message.content.")
        return content.strip()
