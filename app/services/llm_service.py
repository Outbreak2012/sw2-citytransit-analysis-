"""
LLM Service - Multi-Provider Language Model Service
=====================================================
Servicio de LLM que soporta múltiples proveedores:
1. Ollama (local) - Sin API key, gratis, privado
2. HuggingFace - Modelos open-source en la nube
3. Groq - API gratis con rate limits
4. OpenAI - Cuando hay API key configurada

Prioridad por defecto: Ollama > HuggingFace > Groq > OpenAI
"""
import logging
import asyncio
import httpx
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Proveedores de LLM soportados."""
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    GROQ = "groq"
    OPENAI = "openai"


@dataclass
class LLMResponse:
    """Respuesta del LLM."""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int = 0
    latency_ms: float = 0
    success: bool = True
    error: Optional[str] = None


class BaseLLMProvider(ABC):
    """Clase base para proveedores de LLM."""
    
    @property
    @abstractmethod
    def provider_name(self) -> LLMProvider:
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs) -> AsyncGenerator[str, None]:
        pass


class OllamaProvider(BaseLLMProvider):
    """
    Ollama - LLM Local
    Requiere: ollama corriendo localmente (ollama serve)
    Modelos recomendados: llama3.2, mistral, codellama, phi3
    """
    
    def __init__(self):
        self.base_url = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434')
        self.model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2')
        self._available: Optional[bool] = None
    
    @property
    def provider_name(self) -> LLMProvider:
        return LLMProvider.OLLAMA
    
    @property
    def is_available(self) -> bool:
        if self._available is None:
            self._available = self._check_availability()
        return self._available
    
    def _check_availability(self) -> bool:
        """Verificar si Ollama está corriendo."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        """Generar respuesta con Ollama."""
        import time
        start = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": kwargs.get("model", self.model),
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", 0),
                        "num_predict": kwargs.get("max_tokens", 1024),
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return LLMResponse(
                        content=data.get("response", ""),
                        provider=self.provider_name,
                        model=self.model,
                        tokens_used=data.get("eval_count", 0),
                        latency_ms=(time.time() - start) * 1000,
                        success=True
                    )
                else:
                    return LLMResponse(
                        content="",
                        provider=self.provider_name,
                        model=self.model,
                        latency_ms=(time.time() - start) * 1000,
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text}"
                    )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                latency_ms=(time.time() - start) * 1000,
                success=False,
                error=str(e)
            )
    
    async def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs) -> AsyncGenerator[str, None]:
        """Generar respuesta con streaming."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": kwargs.get("model", self.model),
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": True,
                    "options": {
                        "temperature": kwargs.get("temperature", 0),
                    }
                }
                
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            import json
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
        except Exception as e:
            yield f"[Error: {e}]"


class HuggingFaceProvider(BaseLLMProvider):
    """
    HuggingFace Inference API
    Usa modelos open-source gratuitos (con rate limits)
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'HUGGINGFACE_API_KEY', None)
        self.model = getattr(settings, 'HUGGINGFACE_MODEL', 'mistralai/Mistral-7B-Instruct-v0.2')
        self.base_url = "https://api-inference.huggingface.co/models"
        self._available: Optional[bool] = None
    
    @property
    def provider_name(self) -> LLMProvider:
        return LLMProvider.HUGGINGFACE
    
    @property
    def is_available(self) -> bool:
        # HuggingFace funciona sin API key pero con rate limits
        return True
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        """Generar con HuggingFace Inference API."""
        import time
        start = time.time()
        
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/{self.model}",
                    headers=headers,
                    json={
                        "inputs": full_prompt,
                        "parameters": {
                            "max_new_tokens": kwargs.get("max_tokens", 512),
                            "temperature": kwargs.get("temperature", 0.1),
                            "return_full_text": False,
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    text = data[0].get("generated_text", "") if isinstance(data, list) else ""
                    return LLMResponse(
                        content=text,
                        provider=self.provider_name,
                        model=self.model,
                        latency_ms=(time.time() - start) * 1000,
                        success=True
                    )
                else:
                    return LLMResponse(
                        content="",
                        provider=self.provider_name,
                        model=self.model,
                        latency_ms=(time.time() - start) * 1000,
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text}"
                    )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                latency_ms=(time.time() - start) * 1000,
                success=False,
                error=str(e)
            )
    
    async def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs) -> AsyncGenerator[str, None]:
        """HuggingFace no soporta streaming nativo, simular con chunks."""
        response = await self.generate(prompt, system_prompt, **kwargs)
        # Simular streaming dividiendo la respuesta
        words = response.content.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.02)


class GroqProvider(BaseLLMProvider):
    """
    Groq - API gratuita ultrarrápida
    Requiere GROQ_API_KEY (gratis en console.groq.com)
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'GROQ_API_KEY', None)
        self.model = getattr(settings, 'GROQ_MODEL', 'llama-3.1-8b-instant')
        self.base_url = "https://api.groq.com/openai/v1"
    
    @property
    def provider_name(self) -> LLMProvider:
        return LLMProvider.GROQ
    
    @property
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        """Generar con Groq API."""
        import time
        start = time.time()
        
        if not self.api_key:
            return LLMResponse(
                content="", provider=self.provider_name, model=self.model,
                success=False, error="GROQ_API_KEY no configurada"
            )
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt} if system_prompt else None,
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": kwargs.get("temperature", 0),
                        "max_tokens": kwargs.get("max_tokens", 1024),
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return LLMResponse(
                        content=content,
                        provider=self.provider_name,
                        model=self.model,
                        tokens_used=data.get("usage", {}).get("total_tokens", 0),
                        latency_ms=(time.time() - start) * 1000,
                        success=True
                    )
                else:
                    return LLMResponse(
                        content="",
                        provider=self.provider_name,
                        model=self.model,
                        latency_ms=(time.time() - start) * 1000,
                        success=False,
                        error=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                latency_ms=(time.time() - start) * 1000,
                success=False,
                error=str(e)
            )
    
    async def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs) -> AsyncGenerator[str, None]:
        """Streaming con Groq."""
        if not self.api_key:
            yield "[Error: GROQ_API_KEY no configurada]"
            return
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt} if system_prompt else None,
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": kwargs.get("temperature", 0),
                        "stream": True,
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            import json
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
        except Exception as e:
            yield f"[Error: {e}]"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI - Requiere OPENAI_API_KEY."""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
    
    @property
    def provider_name(self) -> LLMProvider:
        return LLMProvider.OPENAI
    
    @property
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        """Generar con OpenAI."""
        import time
        start = time.time()
        
        if not self.api_key:
            return LLMResponse(
                content="", provider=self.provider_name, model=self.model,
                success=False, error="OPENAI_API_KEY no configurada"
            )
        
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage
            
            llm = ChatOpenAI(
                model=self.model,
                temperature=kwargs.get("temperature", 0),
                api_key=self.api_key,
            )
            
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            
            response = llm.invoke(messages)
            
            return LLMResponse(
                content=response.content,
                provider=self.provider_name,
                model=self.model,
                latency_ms=(time.time() - start) * 1000,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                latency_ms=(time.time() - start) * 1000,
                success=False,
                error=str(e)
            )
    
    async def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs) -> AsyncGenerator[str, None]:
        """Streaming con OpenAI."""
        if not self.api_key:
            yield "[Error: OPENAI_API_KEY no configurada]"
            return
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                async with client.stream(
                    "POST",
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": kwargs.get("temperature", 0),
                        "stream": True,
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            import json
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
        except Exception as e:
            yield f"[Error: {e}]"


class LLMService:
    """
    Servicio unificado de LLM con fallback automático.
    Prioridad: Ollama > Groq > HuggingFace > OpenAI
    """
    
    def __init__(self):
        self.providers: List[BaseLLMProvider] = [
            OllamaProvider(),
            GroqProvider(),
            HuggingFaceProvider(),
            OpenAIProvider(),
        ]
        self._active_provider: Optional[BaseLLMProvider] = None
        self._initialize()
    
    def _initialize(self):
        """Detectar el primer proveedor disponible."""
        for provider in self.providers:
            if provider.is_available:
                self._active_provider = provider
                logger.info(f"LLM Service: Usando {provider.provider_name.value}")
                break
        
        if not self._active_provider:
            logger.warning("LLM Service: Ningún proveedor disponible. Usando regex fallback.")
    
    @property
    def active_provider(self) -> Optional[BaseLLMProvider]:
        return self._active_provider
    
    @property
    def is_available(self) -> bool:
        return self._active_provider is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Estado de todos los proveedores."""
        return {
            "active_provider": self._active_provider.provider_name.value if self._active_provider else None,
            "providers": [
                {
                    "name": p.provider_name.value,
                    "available": p.is_available,
                    "active": p == self._active_provider
                }
                for p in self.providers
            ]
        }
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: str = "",
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generar respuesta del LLM.
        
        Args:
            prompt: El prompt del usuario
            system_prompt: Instrucciones del sistema
            provider: Forzar un proveedor específico
            **kwargs: temperature, max_tokens, etc.
        """
        # Si se especifica proveedor, usarlo
        if provider:
            for p in self.providers:
                if p.provider_name == provider:
                    if p.is_available:
                        return await p.generate(prompt, system_prompt, **kwargs)
                    else:
                        return LLMResponse(
                            content="",
                            provider=provider,
                            model="",
                            success=False,
                            error=f"Proveedor {provider.value} no disponible"
                        )
        
        # Usar proveedor activo con fallback
        for p in self.providers:
            if p.is_available:
                result = await p.generate(prompt, system_prompt, **kwargs)
                if result.success:
                    return result
                logger.warning(f"LLM {p.provider_name.value} falló: {result.error}, probando siguiente...")
        
        return LLMResponse(
            content="",
            provider=LLMProvider.OLLAMA,
            model="",
            success=False,
            error="Ningún proveedor LLM disponible"
        )
    
    async def generate_stream(
        self, 
        prompt: str, 
        system_prompt: str = "",
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generar respuesta con streaming."""
        target = None
        
        if provider:
            for p in self.providers:
                if p.provider_name == provider and p.is_available:
                    target = p
                    break
        else:
            target = self._active_provider
        
        if target:
            async for chunk in target.generate_stream(prompt, system_prompt, **kwargs):
                yield chunk
        else:
            yield "[Error: Ningún proveedor LLM disponible]"


# Instancia global
llm_service = LLMService()
