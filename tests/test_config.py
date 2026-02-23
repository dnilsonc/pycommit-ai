import os
from unittest import mock

import pytest
from pycommit_ai.config import get_config, BUILTIN_SERVICES

def test_default_config():
    with mock.patch("pycommit_ai.config.Path.exists") as mock_exists:
        # Mock empty config
        mock_exists.return_value = False
        
        config = get_config()
        
        assert config["locale"] == "en"
        assert config["generate"] == 1
        assert config["type"] == "conventional"
        assert config["maxLength"] == 50
        
        assert config["GEMINI"]["model"] == ["gemini-2.5-flash"]
        assert config["OPENAI"]["model"] == ["gpt-4o-mini"]

def test_cli_overrides():
    with mock.patch("pycommit_ai.config.Path.exists") as mock_exists:
        mock_exists.return_value = False
        
        config = get_config({"locale": "pt", "OPENAI.model": "gpt-4"})
        
        assert config["locale"] == "pt"
        assert config["OPENAI"]["model"] == ["gpt-4"]

def test_env_vars():
    with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-123"}):
        with mock.patch("pycommit_ai.config.Path.exists") as mock_exists:
            mock_exists.return_value = False
            
            config = get_config()
            assert config["GEMINI"]["key"] == "test-key-123"
