from __future__ import annotations

import os

from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

load_dotenv()

DEFAULT_MODEL = "openai/deepseek-ai/deepseek-v4-flash"


def zentao_model() -> LiteLlm:
    """Build the shared LiteLLM model used by Zentao ADK agents."""
    return LiteLlm(model=os.getenv("ZENTAO_AGENT_MODEL", DEFAULT_MODEL))
