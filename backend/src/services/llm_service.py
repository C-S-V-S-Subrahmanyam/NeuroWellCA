"""
LLM service that routes generation to the globally active provider.
"""

from __future__ import annotations

from typing import Optional
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import LlmProvider
from src.utils.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Resolve active provider and generate a completion."""

    async def _get_active_provider(self, db: AsyncSession) -> Optional[LlmProvider]:
        result = await db.execute(
            select(LlmProvider)
            .where(LlmProvider.deleted_at == None, LlmProvider.is_active == True)
            .order_by(LlmProvider.is_default.desc(), LlmProvider.updated_at.desc(), LlmProvider.id.desc())
        )
        return result.scalars().first()

    async def get_active_provider_info(self, db: AsyncSession) -> Optional[dict]:
        """Return active provider metadata for diagnostics/admin UX."""
        provider = await self._get_active_provider(db)
        if not provider:
            return None
        cfg = provider.config or {}
        return {
            "id": provider.id,
            "name": provider.name,
            "provider_type": provider.provider_type,
            "model": cfg.get("model") or (provider.models[0] if provider.models else settings.OLLAMA_MODEL),
            "has_api_key": bool((provider.api_key_encrypted or "").strip()),
            "base_url": provider.base_url,
        }

    @staticmethod
    def _context_prompt(prompt: str, context: Optional[list[str]]) -> str:
        if not context:
            return prompt
        context_text = "\n".join(context[-10:])
        return f"Previous conversation:\n{context_text}\n\nUser: {prompt}\n\nAssistant:"

    async def _call_ollama(self, prompt: str, model: str, base_url: str) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 512},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{base_url.rstrip('/')}/api/generate", json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Ollama error {response.status_code}: {response.text}")
        return response.json().get("response", "I'm here to support you.")

    async def _call_openai_compatible(
        self,
        prompt: str,
        model: str,
        base_url: str,
        api_key: str,
    ) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 512,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
        if response.status_code != 200:
            raise RuntimeError(f"OpenAI-compatible error {response.status_code}: {response.text}")
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return "I'm here to support you."
        return choices[0].get("message", {}).get("content", "I'm here to support you.")

    async def _call_gemini(self, prompt: str, model: str, base_url: str, api_key: str) -> str:
        endpoint = f"{base_url.rstrip('/')}/models/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "topP": 0.9, "maxOutputTokens": 512},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                endpoint,
                params={"key": api_key},
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        if response.status_code != 200:
            raise RuntimeError(f"Gemini error {response.status_code}: {response.text}")
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return "I'm here to support you."
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return "I'm here to support you."
        return parts[0].get("text", "I'm here to support you.")

    async def generate_response(self, db: AsyncSession, prompt: str, context: Optional[list[str]] = None) -> str:
        """Generate response using active provider; fallback to configured Ollama."""
        full_prompt = self._context_prompt(prompt, context)
        provider = await self._get_active_provider(db)

        if provider is None:
            logger.info("No active LLM provider in DB. Falling back to app Ollama config.")
            return await self._call_ollama(full_prompt, settings.OLLAMA_MODEL, settings.OLLAMA_API_URL)

        provider_type = (provider.provider_type or "").strip().lower()
        cfg = provider.config or {}
        model = cfg.get("model") or (provider.models[0] if provider.models else settings.OLLAMA_MODEL)
        base_url = provider.base_url or ""
        api_key = (provider.api_key_encrypted or "").strip()

        try:
            if provider_type == "ollama":
                return await self._call_ollama(
                    full_prompt,
                    model,
                    base_url or settings.OLLAMA_API_URL,
                )

            if provider_type in {"openai", "chatgpt"}:
                return await self._call_openai_compatible(
                    full_prompt,
                    model,
                    base_url or "https://api.openai.com/v1",
                    api_key,
                )

            if provider_type == "deepseek":
                return await self._call_openai_compatible(
                    full_prompt,
                    model,
                    base_url or "https://api.deepseek.com/v1",
                    api_key,
                )

            if provider_type == "gemini":
                return await self._call_gemini(
                    full_prompt,
                    model,
                    base_url or "https://generativelanguage.googleapis.com/v1beta",
                    api_key,
                )

            if provider_type == "ollama-local":
                return await self._call_ollama(
                    full_prompt,
                    model,
                    base_url or settings.OLLAMA_API_URL,
                )

            # Custom providers are treated as OpenAI-compatible by default.
            return await self._call_openai_compatible(
                full_prompt,
                model,
                base_url or "https://api.openai.com/v1",
                api_key,
            )
        except Exception as exc:
            logger.error("Provider %s failed, fallback to Ollama: %s", provider.name, exc)
            return await self._call_ollama(full_prompt, settings.OLLAMA_MODEL, settings.OLLAMA_API_URL)


llm_service = LLMService()
