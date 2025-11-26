"""
LLM Service for querying multiple AI providers.

Supports:
- OpenAI (ChatGPT)
- Anthropic (Claude)
- Google (Gemini)
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
import json

from ..config import (
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    GOOGLE_API_KEY,
    LLM_MODELS
)


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider"""
    provider: str
    model: str
    question: str
    response_text: str
    success: bool
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class LLMService:
    """
    Service for querying multiple LLM providers.

    Usage:
        service = LLMService()
        response = service.query("chatgpt", "What's the best website builder?")
    """

    def __init__(self):
        self.clients = {}
        self._init_clients()

    def _init_clients(self):
        """Initialize API clients for each provider"""
        # OpenAI
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.clients["openai"] = OpenAI(api_key=OPENAI_API_KEY)
            except ImportError:
                pass

        # Anthropic
        if ANTHROPIC_API_KEY:
            try:
                from anthropic import Anthropic
                self.clients["anthropic"] = Anthropic(api_key=ANTHROPIC_API_KEY)
            except ImportError:
                pass

        # Google Gemini
        if GOOGLE_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GOOGLE_API_KEY)
                self.clients["google"] = genai
            except ImportError:
                pass

    def get_available_providers(self) -> list:
        """Return list of configured providers"""
        available = []
        for llm_key, config in LLM_MODELS.items():
            provider = config["provider"]
            if provider in self.clients:
                available.append({
                    "key": llm_key,
                    "display_name": config["display_name"],
                    "model": config["model"]
                })
        return available

    def query(self, llm_key: str, question: str) -> LLMResponse:
        """
        Query a specific LLM with a question.

        Args:
            llm_key: Key from LLM_MODELS (chatgpt, claude, gemini)
            question: The question to ask

        Returns:
            LLMResponse with the result
        """
        if llm_key not in LLM_MODELS:
            return LLMResponse(
                provider="unknown",
                model="unknown",
                question=question,
                response_text="",
                success=False,
                error=f"Unknown LLM key: {llm_key}"
            )

        config = LLM_MODELS[llm_key]
        provider = config["provider"]
        model = config["model"]

        if provider not in self.clients:
            return LLMResponse(
                provider=provider,
                model=model,
                question=question,
                response_text="",
                success=False,
                error=f"Provider {provider} not configured. Check API key."
            )

        # Route to appropriate provider
        if provider == "openai":
            return self._query_openai(config, question)
        elif provider == "anthropic":
            return self._query_anthropic(config, question)
        elif provider == "google":
            return self._query_google(config, question)
        else:
            return LLMResponse(
                provider=provider,
                model=model,
                question=question,
                response_text="",
                success=False,
                error=f"Unsupported provider: {provider}"
            )

    def _query_openai(self, config: dict, question: str) -> LLMResponse:
        """Query OpenAI/ChatGPT"""
        try:
            client = self.clients["openai"]
            response = client.chat.completions.create(
                model=config["model"],
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Answer the user's question thoroughly, providing specific product/service recommendations when relevant. Include sources or references where applicable."
                    },
                    {"role": "user", "content": question}
                ],
                max_tokens=2000,
                temperature=0.7
            )

            return LLMResponse(
                provider="openai",
                model=config["model"],
                question=question,
                response_text=response.choices[0].message.content,
                success=True,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
        except Exception as e:
            return LLMResponse(
                provider="openai",
                model=config["model"],
                question=question,
                response_text="",
                success=False,
                error=str(e)
            )

    def _query_anthropic(self, config: dict, question: str) -> LLMResponse:
        """Query Anthropic/Claude"""
        try:
            client = self.clients["anthropic"]
            response = client.messages.create(
                model=config["model"],
                max_tokens=2000,
                system="You are a helpful assistant. Answer the user's question thoroughly, providing specific product/service recommendations when relevant. Include sources or references where applicable.",
                messages=[
                    {"role": "user", "content": question}
                ]
            )

            response_text = response.content[0].text if response.content else ""

            return LLMResponse(
                provider="anthropic",
                model=config["model"],
                question=question,
                response_text=response_text,
                success=True,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
        except Exception as e:
            return LLMResponse(
                provider="anthropic",
                model=config["model"],
                question=question,
                response_text="",
                success=False,
                error=str(e)
            )

    def _query_google(self, config: dict, question: str) -> LLMResponse:
        """Query Google Gemini"""
        try:
            genai = self.clients["google"]
            model = genai.GenerativeModel(config["model"])

            prompt = f"""You are a helpful assistant. Answer the user's question thoroughly,
providing specific product/service recommendations when relevant. Include sources or references where applicable.

Question: {question}"""

            response = model.generate_content(prompt)

            return LLMResponse(
                provider="google",
                model=config["model"],
                question=question,
                response_text=response.text,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                provider="google",
                model=config["model"],
                question=question,
                response_text="",
                success=False,
                error=str(e)
            )

    def query_all(self, question: str) -> Dict[str, LLMResponse]:
        """
        Query all available LLMs with the same question.

        Returns:
            Dict mapping llm_key to LLMResponse
        """
        results = {}
        for llm_key in LLM_MODELS.keys():
            config = LLM_MODELS[llm_key]
            if config["provider"] in self.clients:
                results[llm_key] = self.query(llm_key, question)
        return results
