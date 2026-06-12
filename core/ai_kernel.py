"""
core/ai_kernel.py — Finaler Merge-Stand v3.2.1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MIGRATION ABGESCHLOSSEN:
  Kanonische Implementierung → modules/kernel/ai_kernel/ai_kernel.py

Dieses Modul ist ein vollständiger Backwards-Compat-Shim.
Alle Klassen, Enums und Funktionen sind weiterhin importierbar —
sie leiten intern auf das kanonische Modul weiter.

Bitte Imports ab sofort auf den neuen Pfad aktualisieren:
  from modules.kernel.ai_kernel.ai_kernel import (
      AIKernel, AIRequest, AIResponse,
      LLMRouter, ReasoningEngine,
      InferenceMode, DecisionType,
      constitutional_check, CONSTITUTIONAL_RULES,
      get_ai_kernel,
  )
"""
import warnings as _warnings

_warnings.warn(
    "\n[DEPRECATED v3.2.1] core.ai_kernel wurde nach "
    "modules.kernel.ai_kernel.ai_kernel verschoben.\n"
    "Bitte Import aktualisieren — dieser Shim wird in v4.0 entfernt.",
    DeprecationWarning,
    stacklevel=2,
)

# ── Re-Exports ────────────────────────────────────────────────────────────────
from modules.kernel.ai_kernel.ai_kernel import (  # noqa: F401, E402
    # Klassen
    AIKernel,
    AIRequest,
    AIResponse,
    LLMRouter,
    ReasoningEngine,
    # Enums
    InferenceMode,
    DecisionType,
    # Funktionen
    constitutional_check,
    get_ai_kernel,
    # Konstanten
    REGISTERED_MODELS,
    CONSTITUTIONAL_RULES,
    HF_API_BASE,
)

# ── Legacy-Aliase (core/ai_kernel hatte andere Namen) ─────────────────────────
InferenceRequest = AIRequest    # noqa: F811
InferenceResult  = AIResponse   # noqa: F811

# ── Sentinel damit andere Module sehen dass Merge vollzogen ist ───────────────
_MERGE_STATUS  = "COMPLETED"
_MERGE_VERSION = "3.2.1"
_CANONICAL_PATH = "modules.kernel.ai_kernel.ai_kernel"

__all__ = [
    "AIKernel", "AIRequest", "AIResponse",
    "LLMRouter", "ReasoningEngine",
    "InferenceMode", "DecisionType",
    "constitutional_check", "get_ai_kernel",
    "REGISTERED_MODELS", "CONSTITUTIONAL_RULES",
    # Legacy
    "InferenceRequest", "InferenceResult",
]
