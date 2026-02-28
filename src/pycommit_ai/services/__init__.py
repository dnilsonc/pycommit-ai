from typing import List

from .base import AIResponse, AIService
from .gemini import GeminiService
from .groq import GroqService
from .openai_service import OpenAIService
from .openrouter import OpenRouterService

__all__ = ["AIResponse", "AIService", "get_available_services"]

def get_available_services(config: dict, diff, branch_name: str) -> List[AIService]:
    """Return an instantiated list of AI services that have API keys configured."""
    services = []
    
    if config.get("GEMINI", {}).get("key"):
        for model in config["GEMINI"].get("model", ["gemini-2.5-flash"]):
            services.append(GeminiService(config, config["GEMINI"], diff, model))
            
    if config.get("OPENAI", {}).get("key"):
        for model in config["OPENAI"].get("model", ["gpt-4o-mini"]):
            services.append(OpenAIService(config, config["OPENAI"], diff, model))
            
    if config.get("GROQ", {}).get("key"):
        for model in config["GROQ"].get("model", ["llama3-8b-8192"]):
            services.append(GroqService(config, config["GROQ"], diff, model))
            
    if config.get("OPENROUTER", {}).get("key"):
        for model in config["OPENROUTER"].get("model", ["google/gemini-2.0-flash-001"]):
            services.append(OpenRouterService(config, config["OPENROUTER"], diff, model))
            
    return services
