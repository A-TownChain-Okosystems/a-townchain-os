"""
AI Kernel Compat-Shim (v3.2.1)
Dieses Modul wurde nach modules/kernel/ai_kernel/ai_kernel.py verschoben.
Bitte Imports aktualisieren auf:
  from modules.kernel.ai_kernel.ai_kernel import AIKernel, AIRequest, AIResponse, get_ai_kernel
"""
import warnings
warnings.warn(
    "core.ai_kernel ist deprecated seit v3.2.1. "
    "Bitte nutze: from modules.kernel.ai_kernel.ai_kernel import AIKernel",
    DeprecationWarning, stacklevel=2,
)
from modules.kernel.ai_kernel.ai_kernel import (  # noqa: F401
    AIKernel, AIRequest, AIResponse,
    LLMRouter, ReasoningEngine,
    InferenceMode, DecisionType,
    constitutional_check, CONSTITUTIONAL_RULES,
    get_ai_kernel,
)
# Legacy-Alias
InferenceRequest = AIRequest
InferenceResult  = AIResponse
