from typing import Any, Dict, List

from groq import Groq, GroqError

from pycommit_ai.errors import AIServiceError
from pycommit_ai.git import GitDiff
from pycommit_ai.services.base import AIResponse, AIService


class GroqService(AIService):
    def __init__(self, config: Dict[str, Any], service_config: Dict[str, Any], diff: GitDiff, model_name: str):
        super().__init__(config, service_config, diff, model_name)
        if not self.api_key:
            raise AIServiceError("Groq API key is required. Run 'pycommit-ai config set GROQ.key=YOUR_KEY'")
        self.client = Groq(api_key=self.api_key)

    def generate_commit_messages(self) -> List[AIResponse]:
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt()

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                n=1,
                max_tokens=int(self.config.get("maxTokens", 1024)),
                temperature=float(self.config.get("temperature", 0.7)),
                top_p=float(self.config.get("topP", 1.0)),
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise AIServiceError("Empty response received from Groq API.")
                
            content = response.choices[0].message.content
            return self.parse_message(content)
        except GroqError as e:
            raise AIServiceError(f"Groq API Error: {str(e)}", original_error=e)
        except Exception as e:
            if isinstance(e, AIServiceError):
                raise e
            raise AIServiceError(f"Unexpected Error during Groq request: {str(e)}", original_error=e)
