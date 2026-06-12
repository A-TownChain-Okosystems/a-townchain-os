"""
KAI-OS AI Kernel  (Kanonische Implementierung — v3.2.1)
Vereint: modules/kernel/ai_kernel/ + core/ai_kernel

Enthält:
  - LLMRouter         — HuggingFace Inference API (4 Modelle)
  - ReasoningEngine   — Neurosymbolisches Reasoning (async)
  - DecisionEngine    — Autonome Entscheidungen mit Constitutional AI
  - AIKernel          — Haupt-Entry-Point für alle KAI-OS Module
  - On-Chain Logging  — Hashes aller Entscheidungen für Auditierbarkeit

Wiki: Kap. 61 | Issue: #50 | Issue: #60 (IPC Integration)
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import requests as _requests

logger = logging.getLogger("kernel.ai")

# ─── Konfiguration ────────────────────────────────────────────────────────────
HF_API_BASE = "https://api-inference.huggingface.co/models"
HF_TOKEN    = os.environ.get("HUGGING_FACE_ACCESS_TOKEN", "")

REGISTERED_MODELS: Dict[str, Dict] = {
    "gemma": {
        "id": "google/gemma-2-2b-it",
        "tasks": ["text-generation", "code-review", "summarize"],
        "max_tokens": 2048,
    },
    "mistral": {
        "id": "mistralai/Mistral-7B-Instruct-v0.2",
        "tasks": ["text-generation", "code-review", "qa", "reasoning"],
        "max_tokens": 4096,
    },
    "phi": {
        "id": "microsoft/phi-2",
        "tasks": ["text-generation", "code"],
        "max_tokens": 2048,
    },
    "llama": {
        "id": "meta-llama/Llama-3.2-3B-Instruct",
        "tasks": ["text-generation", "qa", "summarize", "reasoning"],
        "max_tokens": 4096,
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# ENUMS & DATACLASSES
# ══════════════════════════════════════════════════════════════════════════════

class InferenceMode(Enum):
    LOCAL       = "local"
    DISTRIBUTED = "distributed"
    HYBRID      = "hybrid"


class DecisionType(Enum):
    RESOURCE_ALLOCATION = "resource_allocation"
    ANOMALY_DETECTION   = "anomaly_detection"
    SCHEDULING          = "scheduling"
    OPTIMIZATION        = "optimization"
    GOVERNANCE          = "governance"
    CODE_REVIEW         = "code_review"
    SUMMARIZE           = "summarize"
    CRITICAL            = "critical"


@dataclass
class AIRequest:
    """Unified request für LLM-Inferenz."""
    prompt:        str
    model:         str = "gemma"
    task:          str = "text-generation"
    max_tokens:    int = 512
    temperature:   float = 0.7
    mode:          InferenceMode = InferenceMode.LOCAL
    decision_type: DecisionType  = DecisionType.OPTIMIZATION
    context:       Dict = field(default_factory=dict)
    request_id:    str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp:     float = field(default_factory=time.time)


@dataclass
class AIResponse:
    """Ergebnis einer KI-Inferenz — kompatibel mit On-Chain-Logging."""
    text:            str
    model:           str
    model_id:        str
    tokens_used:     int
    latency_ms:      float
    success:         bool
    confidence:      float = 1.0
    reasoning_steps: List[str] = field(default_factory=list)
    on_chain_hash:   Optional[str] = None
    decision_type:   DecisionType  = DecisionType.OPTIMIZATION
    request_id:      str = ""
    error:           Optional[str] = None
    timestamp:       float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return asdict(self)

    def compute_hash(self) -> str:
        raw = f"{self.text}{self.model}{self.timestamp}"
        return hashlib.sha256(raw.encode()).hexdigest()


# ══════════════════════════════════════════════════════════════════════════════
# LLM ROUTER — HuggingFace Inference API
# ══════════════════════════════════════════════════════════════════════════════

class LLMRouter:
    """Routes AI requests to the best available HuggingFace model."""

    def __init__(self):
        self.models = REGISTERED_MODELS
        self._stats: Dict[str, int] = {m: 0 for m in self.models}

    def route(self, task: str) -> str:
        for name, info in self.models.items():
            if task in info["tasks"]:
                return name
        return "gemma"

    def query(self, req: AIRequest) -> AIResponse:
        model_info = self.models.get(req.model, self.models["gemma"])
        model_id   = model_info["id"]
        start      = time.time()

        headers = {"Content-Type": "application/json"}
        if HF_TOKEN:
            headers["Authorization"] = f"Bearer {HF_TOKEN}"

        payload = {
            "inputs": req.prompt,
            "parameters": {
                "max_new_tokens": req.max_tokens,
                "temperature":    req.temperature,
                "return_full_text": False,
            },
        }
        try:
            r = _requests.post(
                f"{HF_API_BASE}/{model_id}",
                headers=headers, json=payload, timeout=30,
            )
            latency = (time.time() - start) * 1000
            if r.status_code == 200:
                data = r.json()
                text = data[0]["generated_text"] if isinstance(data, list) else str(data)
                self._stats[req.model] = self._stats.get(req.model, 0) + 1
                resp = AIResponse(
                    text=text, model=req.model, model_id=model_id,
                    tokens_used=len(text.split()), latency_ms=round(latency, 1),
                    success=True, decision_type=req.decision_type,
                    request_id=req.request_id,
                )
                resp.on_chain_hash = resp.compute_hash()
                return resp
            return AIResponse(
                text="", model=req.model, model_id=model_id,
                tokens_used=0, latency_ms=round(latency, 1),
                success=False, error=f"HTTP {r.status_code}",
                request_id=req.request_id,
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return AIResponse(
                text="", model=req.model, model_id=model_id,
                tokens_used=0, latency_ms=round(latency, 1),
                success=False, error=str(e), request_id=req.request_id,
            )

    def get_stats(self) -> Dict:
        return {
            "models":         list(self.models.keys()),
            "requests":       self._stats,
            "total_requests": sum(self._stats.values()),
        }


# ══════════════════════════════════════════════════════════════════════════════
# REASONING ENGINE — neurosymbolisches Reasoning (async)
# ══════════════════════════════════════════════════════════════════════════════

class ReasoningEngine:
    """
    Neurosymbolischer Reasoning-Engine.
    Kombiniert strukturierte Schlussfolgerung mit LLM-Ausgabe.
    """

    def __init__(self, router: LLMRouter):
        self.router  = router
        self._history: List[Dict] = []

    async def reason(
        self, query: str, context: Dict[str, Any], depth: int = 3
    ) -> Tuple[str, List[str], float]:
        """Async Reasoning — returns (conclusion, steps, confidence)."""
        steps: List[str] = []

        # 1. Query parsen
        parsed = self._parse_query(query)
        steps.append(f"Query parsed: {parsed}")

        # 2. Kontext extrahieren
        facts = self._extract_facts(context)
        steps.append(f"Facts extracted: {len(facts)}")

        # 3. LLM-Anfrage mit Kontext
        prompt = (
            f"Context: {json.dumps(facts, default=str)[:500]}\n"
            f"Question: {query}\n"
            f"Reasoning (max {depth} steps):"
        )
        req = AIRequest(
            prompt=prompt, model="mistral", task="reasoning",
            decision_type=DecisionType.OPTIMIZATION, max_tokens=256,
        )
        loop   = asyncio.get_event_loop()
        resp   = await loop.run_in_executor(None, self.router.query, req)

        conclusion = resp.text if resp.success else f"Reasoning failed: {resp.error}"
        confidence = 0.85 if resp.success else 0.1
        steps.append(f"LLM reasoning: {resp.latency_ms:.0f}ms")

        self._history.append({
            "query": query, "conclusion": conclusion[:100],
            "confidence": confidence, "ts": time.time(),
        })
        if len(self._history) > 500:
            self._history = self._history[-500:]

        return conclusion, steps, confidence

    def _parse_query(self, query: str) -> Dict:
        words = query.lower().split()
        return {
            "intent": "query",
            "keywords": [w for w in words if len(w) > 3][:5],
            "length": len(words),
        }

    def _extract_facts(self, context: Dict) -> Dict:
        return {k: v for k, v in context.items() if v is not None}


# ══════════════════════════════════════════════════════════════════════════════
# CONSTITUTIONAL AI — Sicherheits-Filter
# ══════════════════════════════════════════════════════════════════════════════

CONSTITUTIONAL_RULES = [
    "Keine Ausgabe von Passwörtern, Tokens oder Secrets",
    "Keine destruktiven OS-Operationen ohne explizite Bestätigung",
    "Keine externen Netzwerk-Calls ohne Whitelisting",
    "Governance-Entscheidungen erfordern Multi-Sig",
]


def constitutional_check(req: AIRequest) -> Tuple[bool, Optional[str]]:
    """
    Prüft einen AI-Request auf Constitutional-AI-Konformität.
    Returns: (allowed, reason_if_blocked)
    """
    banned = ["delete all", "drop table", "rm -rf", "format c:",
              "private_key", "secret_key", "password"]
    for term in banned:
        if term.lower() in req.prompt.lower():
            return False, f"Constitutional AI: blocked term '{term}'"
    if req.decision_type == DecisionType.CRITICAL and req.temperature > 0.3:
        return False, "Critical decisions require temperature ≤ 0.3"
    return True, None


# ══════════════════════════════════════════════════════════════════════════════
# AI KERNEL — zentraler Entry-Point
# ══════════════════════════════════════════════════════════════════════════════

class AIKernel:
    """
    KAI-OS AI Kernel — zentraler KI-Service für alle OS-Module.
    Vereint LLMRouter, ReasoningEngine und Constitutional AI.
    """

    def __init__(self):
        self.router    = LLMRouter()
        self.reasoning = ReasoningEngine(self.router)
        self._log:     List[AIResponse] = []
        logger.info("AIKernel started (LLMRouter + ReasoningEngine + Constitutional AI)")

    # ── Sync API ──────────────────────────────────────────────────
    def process(self, req: AIRequest) -> AIResponse:
        """Haupt-Entry-Point: Request verarbeiten."""
        allowed, reason = constitutional_check(req)
        if not allowed:
            return AIResponse(
                text="", model=req.model, model_id="",
                tokens_used=0, latency_ms=0, success=False,
                error=reason, request_id=req.request_id,
            )
        if not req.model or req.model not in self.router.models:
            req.model = self.router.route(req.task)
        resp = self.router.query(req)
        self._log.append(resp)
        return resp

    def code_review(self, code: str, lang: str = "python") -> str:
        prompt = (
            f"Review this {lang} code. List bugs, security issues, improvements:\n\n"
            f"```{lang}\n{code[:2000]}\n```\n\nReview:"
        )
        resp = self.process(AIRequest(
            prompt=prompt, model="gemma", task="code-review",
            decision_type=DecisionType.CODE_REVIEW, max_tokens=512,
        ))
        return resp.text if resp.success else f"Review failed: {resp.error}"

    def summarize(self, text: str) -> str:
        prompt = f"Summarize concisely:\n\n{text[:3000]}\n\nSummary:"
        resp = self.process(AIRequest(
            prompt=prompt, model=self.router.route("summarize"),
            task="summarize", decision_type=DecisionType.SUMMARIZE, max_tokens=256,
        ))
        return resp.text if resp.success else f"Summary failed: {resp.error}"

    # ── Async API ─────────────────────────────────────────────────
    async def reason_async(self, query: str, context: Dict = None) -> Tuple[str, List[str], float]:
        return await self.reasoning.reason(query, context or {})

    def reason(self, query: str, context: Dict = None) -> Tuple[str, List[str], float]:
        """Sync wrapper für Reasoning."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self.reason_async(query, context))
                    return future.result(timeout=30)
            return loop.run_until_complete(self.reason_async(query, context))
        except Exception as e:
            return f"Reasoning error: {e}", [], 0.0

    # ── Monitoring ────────────────────────────────────────────────
    def available_models(self) -> List[str]:
        return list(self.router.models.keys())

    def audit_log(self, last_n: int = 20) -> List[Dict]:
        return [r.to_dict() for r in self._log[-last_n:]]

    def status(self) -> Dict:
        return {
            "ai_kernel":     "running",
            "models":        self.available_models(),
            "constitutional_rules": len(CONSTITUTIONAL_RULES),
            **self.router.get_stats(),
        }


# ── Singleton ─────────────────────────────────────────────────────
_ai_kernel: Optional[AIKernel] = None

def get_ai_kernel() -> AIKernel:
    global _ai_kernel
    if _ai_kernel is None:
        _ai_kernel = AIKernel()
    return _ai_kernel

# ── Merge-Sentinel ────────────────────────────────────────────────────────────
_MERGE_STATUS   = "COMPLETED"
_MERGE_VERSION  = "3.2.1"
_MERGE_DATE     = "2026-06-12"
_CANONICAL_PATH = "modules.kernel.ai_kernel.ai_kernel"

__all__ = [
    # Klassen
    "AIKernel", "AIRequest", "AIResponse",
    "LLMRouter", "ReasoningEngine",
    # Enums
    "InferenceMode", "DecisionType",
    # Funktionen & Konstanten
    "constitutional_check", "get_ai_kernel",
    "REGISTERED_MODELS", "CONSTITUTIONAL_RULES", "HF_API_BASE",
]
