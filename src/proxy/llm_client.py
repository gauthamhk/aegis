import asyncio
from typing import Optional

import google.generativeai as genai
from groq import AsyncGroq
from openai import AsyncOpenAI

from src.utils.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

PROVIDER_MODELS = {
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "moonshotai/kimi-k2",
}


class LLMClient:
    def __init__(self):
        self._gemini_configured = False
        self._groq_client: AsyncGroq | None = None
        self._openrouter_client: AsyncOpenAI | None = None

    def _init_gemini(self):
        if not self._gemini_configured and settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self._gemini_configured = True

    def _get_groq(self) -> AsyncGroq:
        if self._groq_client is None:
            self._groq_client = AsyncGroq(api_key=settings.groq_api_key)
        return self._groq_client

    def _get_openrouter(self) -> AsyncOpenAI:
        if self._openrouter_client is None:
            self._openrouter_client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.openrouter_api_key,
            )
        return self._openrouter_client

    async def generate(
        self,
        prompt: str,
        provider: str = "gemini",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_prompt: Optional[str] = None,
    ) -> str:
        model = model or PROVIDER_MODELS.get(provider, PROVIDER_MODELS["gemini"])

        if provider == "gemini":
            return await self._generate_gemini(prompt, model, temperature, max_tokens, system_prompt)
        elif provider == "groq":
            return await self._generate_groq(prompt, model, temperature, max_tokens, system_prompt)
        elif provider == "openrouter":
            return await self._generate_openrouter(prompt, model, temperature, max_tokens, system_prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _generate_gemini(
        self, prompt: str, model: str, temperature: float, max_tokens: int, system_prompt: str | None
    ) -> str:
        self._init_gemini()
        gen_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_prompt,
        )
        response = await asyncio.to_thread(
            gen_model.generate_content,
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text

    async def _generate_groq(
        self, prompt: str, model: str, temperature: float, max_tokens: int, system_prompt: str | None
    ) -> str:
        client = self._get_groq()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def _generate_openrouter(
        self, prompt: str, model: str, temperature: float, max_tokens: int, system_prompt: str | None
    ) -> str:
        client = self._get_openrouter()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def generate_multiple(
        self,
        prompt: str,
        n: int = 5,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> list[str]:
        providers = ["gemini", "groq", "openrouter"]
        tasks = []
        for i in range(n):
            provider = providers[i % len(providers)]
            tasks.append(self.generate(prompt, provider=provider, temperature=temperature, max_tokens=max_tokens))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, str)]


llm_client = LLMClient()
