"""
KAI-OS Kernel — AI Kernel
LLM Router + HuggingFace Model Integration.
Issue: #50 | Wiki: Kap. 61
"""
import os
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger("kernel.ai")

HF_API_BASE = "https://api-inference.huggingface.co/models"
HF_TOKEN    = os.environ.get("HUGGING_FACE_ACCESS_TOKEN", "")

REGISTERED_MODELS = {
    "gemma": {
        "id": "google/gemma-2-2b-it",
        "tasks": ["text-generation", "code-review", "summarize"],
        "max_tokens": 2048,
    },
    "mistral": {
        "id": "mistralai/Mistral-7B-Instruct-v0.2",
        "tasks": ["text-generation", "code-review", "qa"],
        "max_tokens": 4096,
    },
    "phi": {
        "id": "microsoft/phi-2",
        "tasks": ["text-generation", "code"],
        "max_tokens": 2048,
    },
    "llama": {
        "id": "meta-llama/Llama-3.2-3B-Instruct",
        "tasks": ["text-generation", "qa", "summarize"],
        "max_tokens": 4096,
    },
}


@dataclass
class AIRequest:
    prompt: str
    model: str = "gemma"
    task: str = "text-generation"
    max_tokens: int = 512
    temperature: float = 0.7
    context: Dict = field(default_factory=dict)


@dataclass
class AIResponse:
    text: str
    model: str
    model_id: str
    tokens_used: int
    latency_ms: float
    success: bool
    error: Optional[str] = None


class LLMRouter:
    """Routes AI requests to the best available HuggingFace model."""

    def __init__(self):
        self.models = REGISTERED_MODELS
        self._cache: Dict[str, AIResponse] = {}
        self._stats: Dict[str, int] = {m: 0 for m in self.models}
        logger.info(f"LLMRouter initialized with {len(self.models)} models")

    def route(self, task: str) -> str:
        """Return best model name for a given task."""
        for name, info in self.models.items():
            if task in info["tasks"]:
                return name
        return "gemma"  # default fallback

    def query(self, req: AIRequest) -> AIResponse:
        """Send request to HuggingFace Inference API."""
        model_info = self.models.get(req.model, self.models["gemma"])
        model_id = model_info["id"]
        start = time.time()

        headers = {"Content-Type": "application/json"}
        if HF_TOKEN:
            headers["Authorization"] = f"Bearer {HF_TOKEN}"

        payload = {
            "inputs": req.prompt,
            "parameters": {
                "max_new_tokens": req.max_tokens,
                "temperature": req.temperature,
                "return_full_text": False,
            }
        }

        try:
            r = requests.post(
                f"{HF_API_BASE}/{model_id}",
                headers=headers,
                json=payload,
                timeout=30
            )
            latency = (time.time() - start) * 1000
            if r.status_code == 200:
                data = r.json()
                text = data[0]["generated_text"] if isinstance(data, list) else str(data)
                self._stats[req.model] = self._stats.get(req.model, 0) + 1
                return AIResponse(
                    text=text, model=req.model, model_id=model_id,
                    tokens_used=len(text.split()), latency_ms=round(latency, 1),
                    success=True
                )
            else:
                return AIResponse(
                    text="", model=req.model, model_id=model_id,
                    tokens_used=0, latency_ms=round(latency, 1),
                    success=False, error=f"HTTP {r.status_code}"
                )
        except Exception as e:
            latency = (time.time() - start) * 1000
            logger.error(f"LLMRouter.query error: {e}")
            return AIResponse(
                text="", model=req.model, model_id=model_id,
                tokens_used=0, latency_ms=round(latency, 1),
                success=False, error=str(e)
            )

    def code_review(self, code: str, language: str = "python") -> AIResponse:
        """Review code and return suggestions."""
        prompt = (
            f"Review the following {language} code. "
            "List bugs, security issues, and improvements concisely:

"
            f"```{language}
{code[:2000]}
```

Review:"
        )
        return self.query(AIRequest(prompt=prompt, model="gemma", task="code-review", max_tokens=512))

    def summarize(self, text: str) -> AIResponse:
        """Summarize text."""
        prompt = f"Summarize concisely:

{text[:3000]}

Summary:"
        model = self.route("summarize")
        return self.query(AIRequest(prompt=prompt, model=model, task="summarize", max_tokens=256))

    def get_stats(self) -> Dict:
        return {
            "models": list(self.models.keys()),
            "requests": self._stats,
            "total_requests": sum(self._stats.values()),
        }


class AIKernel:
    """KAI-OS AI Kernel — central AI service for all OS modules."""

    def __init__(self):
        self.router = LLMRouter()
        logger.info("AIKernel started")

    def process(self, req: AIRequest) -> AIResponse:
        if not req.model or req.model not in self.router.models:
            req.model = self.router.route(req.task)
        return self.router.query(req)

    def review_code(self, code: str, lang: str = "python") -> str:
        resp = self.router.code_review(code, lang)
        return resp.text if resp.success else f"Review failed: {resp.error}"

    def summarize(self, text: str) -> str:
        resp = self.router.summarize(text)
        return resp.text if resp.success else f"Summary failed: {resp.error}"

    def available_models(self) -> List[str]:
        return list(self.router.models.keys())

    def status(self) -> Dict:
        return {"ai_kernel": "running", **self.router.get_stats()}


_ai_kernel = AIKernel()

def get_ai_kernel() -> AIKernel:
    return _ai_kernel
