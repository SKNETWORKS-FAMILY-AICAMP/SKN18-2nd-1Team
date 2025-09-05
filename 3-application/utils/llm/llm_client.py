# 3-application/utils/llm/llm_client.py
from __future__ import annotations
import os, json
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional
from dotenv import load_dotenv

# .env 로드: 루트(.env) → 3-application/.env  (OS 환경변수 최우선)
APP_ROOT = Path(__file__).resolve().parents[2]   # ← llm → utils → 3-application
REPO_ROOT = APP_ROOT.parent
for p in (REPO_ROOT / ".env", APP_ROOT / ".env"):
    if p.exists():
        load_dotenv(p, override=False)

try:
    from openai import OpenAI
except Exception as e:
    raise RuntimeError("openai 패키지가 필요합니다. `pip install openai`") from e


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name, default)
    return v if v not in ("", None) else default


class LLMClient:
    """OpenAI 전용 간단 클라이언트."""
    def __init__(self) -> None:
        provider = (_env("LLM_PROVIDER", "openai") or "openai").lower()
        if provider != "openai":
            raise NotImplementedError(f"현재는 openai만 지원합니다 (LLM_PROVIDER={provider})")

        api_key = _env("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY가 비어 있습니다. 루트 .env에 키를 넣어주세요.")

        base_url      = _env("OPENAI_BASE_URL")  # 필요 시 프록시/커스텀 엔드포인트
        self.model    = _env("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = float(_env("LLM_TEMPERATURE", "0.1") or 0.1)
        self.max_tokens  = int(_env("LLM_MAX_TOKENS", "600") or 600)
        self.seed        = int(_env("LLM_SEED", "42") or 42)

        self.client = OpenAI(api_key=api_key, base_url=base_url or None)

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        stream: bool = False,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str | Generator[str, None, None]:
        """
        - stream=True  → generator(str) 반환
        - stream=False → 최종 텍스트(str) 반환
        - response_format 지정 시 JSON/object 강제 (chat_json에서 사용)
        """
        args: Dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            seed=self.seed,
        )
        if response_format:
            args["response_format"] = response_format
        args.update(kwargs or {})

        if stream:
            resp = self.client.chat.completions.create(stream=True, **args)

            def _gen():
                for chunk in resp:
                    delta = getattr(chunk.choices[0], "delta", None)
                    if delta and getattr(delta, "content", None):
                        yield delta.content  # type: ignore[attr-defined]
            return _gen()

        resp = self.client.chat.completions.create(stream=False, **args)
        return (resp.choices[0].message.content or "").strip()


# 싱글톤 & 래퍼
_INSTANCE: Optional[LLMClient] = None
def _client() -> LLMClient:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = LLMClient()
    return _INSTANCE

def chat_text(
    messages: List[Dict[str, str]],
    *,
    temperature: Optional[float] = None,
    **kwargs: Any,
) -> str:
    if temperature is not None:
        kwargs["temperature"] = temperature
    return _client().chat(messages, stream=False, **kwargs)  # type: ignore[return-value]

def chat_json(
    messages: List[Dict[str, str]],
    *,
    schema: Optional[Dict[str, Any]] = None,
    temperature: Optional[float] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    if temperature is not None:
        kwargs["temperature"] = temperature
    response_format = (
        {"type": "json_schema", "json_schema": {"name": "response", "schema": schema}}
        if schema else
        {"type": "json_object"}
    )
    text = _client().chat(messages, stream=False, response_format=response_format, **kwargs)  # type: ignore[assignment]
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text}

__all__ = ["LLMClient", "chat_text", "chat_json"]
