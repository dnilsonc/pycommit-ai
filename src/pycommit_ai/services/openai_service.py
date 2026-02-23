from typing import Any, Dict, List

from openai import OpenAI, OpenAIError

from pycommit_ai.errors import AIServiceError
from pycommit_ai.git import GitDiff
from pycommit_ai.services.base import AIResponse, AIService


class OpenAIService(AIService):
    def __init__(self, config: Dict[str, Any], service_config: Dict[str, Any], diff: GitDiff, model_name: str):
        super().__init__(config, service_config, diff, model_name)
        if not self.api_key:
            raise AIServiceError("OpenAI API key is required. Run 'pycommit-ai config set OPENAI.key=YOUR_KEY'")
            
        base_url = self.service_config.get("url", "https://api.openai.com")
        path = self.service_config.get("path", "/v1")
        # Ensure base_url combines with path properly if path is just /v1
        if path and not base_url.endswith(path):
            if path.startswith("/") and base_url.endswith("/"):
                base_url = base_url[:-1] + path
            elif not path.startswith("/") and not base_url.endswith("/"):
                base_url = base_url + "/" + path
            else:
                base_url = base_url + path
                
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url
        )

    def _is_reasoning_model(self, model: str) -> bool:
        """Check if the model is an o1, o3, or gpt-5 reasoning model."""
        model_lower = model.lower()
        prefixes = ["o1", "o3", "gpt-5"]
        return any(
            model_lower == p or model_lower.startswith(f"{p}-") or model_lower.startswith(f"{p}.") 
            for p in prefixes
        )

    def generate_commit_messages(self) -> List[AIResponse]:
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt()

        is_reasoning = self._is_reasoning_model(self.model_name)
        
        kwargs = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "n": 1,
        }

        if is_reasoning:
            kwargs["max_completion_tokens"] = int(self.config.get("maxTokens", 1024))
            # Reasoning usually requires temp=1 and no top_p
            kwargs["temperature"] = 1.0
        else:
            kwargs["max_tokens"] = int(self.config.get("maxTokens", 1024))
            kwargs["temperature"] = float(self.config.get("temperature", 0.7))
            kwargs["top_p"] = float(self.config.get("topP", 1.0))

        try:
            response = self.client.chat.completions.create(**kwargs)
            if not response.choices or not response.choices[0].message.content:
                raise AIServiceError("Empty response received from OpenAI API.")
                
            content = response.choices[0].message.content
            return self.parse_message(content)
        except OpenAIError as e:
            raise AIServiceError(f"OpenAI API Error: {str(e)}", original_error=e)
        except Exception as e:
            if isinstance(e, AIServiceError):
                raise e
            raise AIServiceError(f"Unexpected Error during OpenAI request: {str(e)}", original_error=e)
