import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

from pycommit_ai.errors import AIServiceError
from pycommit_ai.git import GitDiff
from pycommit_ai.prompt import generate_prompt, generate_user_prompt


@dataclass
class AIResponse:
    title: str
    value: str


class AIService(ABC):
    def __init__(self, config: Dict[str, Any], service_config: Dict[str, Any], diff: GitDiff, model_name: str):
        self.config = config
        self.service_config = service_config
        self.diff = diff
        self.model_name = model_name
        self.api_key = service_config.get("key", "")

    @abstractmethod
    def generate_commit_messages(self) -> List[AIResponse]:
        """Generate commit messages from the git diff."""
        pass
        
    def _sanitize_response(self, text: str) -> str:
        """Clean markdown formatting commonly outputted by LLMs."""
        text = text.strip()
        # Remove json markdown indicator
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def parse_message(self, text: str) -> List[AIResponse]:
        """Parse JSON response text into AIResponse objects."""
        text = self._sanitize_response(text)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise AIServiceError(f"Failed to parse JSON response: {text}", original_error=e)
            
        if not isinstance(data, list):
            data = [data]
            
        responses = []
        for item in data:
            if not isinstance(item, dict):
                continue
            subject = item.get("subject", "").strip()
            body = item.get("body", "").strip()
            footer = item.get("footer", "").strip()
            
            if not subject:
                continue
                
            value = subject
            if body:
                value += f"\n\n{body}"
            if footer:
                value += f"\n\n{footer}"
                
            responses.append(AIResponse(title=subject, value=value))
            
        if not responses:
            raise AIServiceError("Did not find any valid commit messages in the response.")
            
        generate_count = int(self.config.get("generate", 1))
        return responses[:generate_count]

    def _get_system_prompt(self) -> str:
        options = {
            "locale": self.config.get("locale"),
            "maxLength": self.config.get("maxLength"),
            "type": self.config.get("type"),
            "generate": self.config.get("generate"),
            "systemPrompt": self.config.get("systemPrompt"),
            "systemPromptPath": self.config.get("systemPromptPath"),
        }
        return generate_prompt(options)
        
    def _get_user_prompt(self) -> str:
        return generate_user_prompt(self.diff.diff)
