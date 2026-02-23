import pytest
from pycommit_ai.services.base import AIService
from pycommit_ai.errors import AIServiceError

class MockAIService(AIService):
    def generate_commit_messages(self):
        return []

def test_parse_message_single():
    service = MockAIService(
        config={"generate": 1},
        service_config={},
        diff=None,
        model_name="mock"
    )
    
    json_text = '''```json
    {
        "subject": "feat(test): add mock",
        "body": "this is a body",
        "footer": "Refs: #1"
    }
    ```'''
    
    responses = service.parse_message(json_text)
    assert len(responses) == 1
    assert responses[0].title == "feat(test): add mock"
    assert "this is a body" in responses[0].value
    assert "Refs: #1" in responses[0].value

def test_parse_message_array():
    service = MockAIService(
        config={"generate": 2},
        service_config={},
        diff=None,
        model_name="mock"
    )
    
    json_text = '''
    [
        {"subject": "msg 1"},
        {"subject": "msg 2", "body": "body"}
    ]
    '''
    
    responses = service.parse_message(json_text)
    assert len(responses) == 2
    assert responses[0].title == "msg 1"
    assert responses[1].title == "msg 2"
    
def test_parse_message_invalid():
    service = MockAIService(
        config={"generate": 1},
        service_config={},
        diff=None,
        model_name="mock"
    )
    
    with pytest.raises(AIServiceError) as excinfo:
        service.parse_message("```This is not json```")
        
    assert "Failed to parse JSON" in str(excinfo.value)
