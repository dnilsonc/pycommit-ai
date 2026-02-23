from typing import Any, Dict, List

from google import genai
from google.genai import types

from pycommit_ai.errors import AIServiceError
from pycommit_ai.git import GitDiff
from pycommit_ai.services.base import AIResponse, AIService


class GeminiService(AIService):
    def __init__(self, config: Dict[str, Any], service_config: Dict[str, Any], diff: GitDiff, model_name: str):
        super().__init__(config, service_config, diff, model_name)
        if not self.api_key:
            raise AIServiceError("Gemini API key is required. Run 'pycommit-ai config set GEMINI.key=YOUR_KEY'")
        self.client = genai.Client(api_key=self.api_key)

    def generate_commit_messages(self) -> List[AIResponse]:
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt()

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=float(self.config.get("temperature", 0.7)),
                    max_output_tokens=int(self.config.get("maxTokens", 2048)),
                    top_p=float(self.config.get("topP", 1.0)),
                    response_mime_type="application/json",
                ),
            )
            
            if not response.text:
                raise AIServiceError("Empty response received from Gemini API.")
                
            return self.parse_message(response.text)
        except Exception as e:
            if isinstance(e, AIServiceError):
                raise e
            raise AIServiceError(f"Gemini API Error: {str(e)}", original_error=e)
