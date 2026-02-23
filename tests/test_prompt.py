from pycommit_ai.prompt import generate_prompt, generate_user_prompt

def test_generate_user_prompt():
    diff = "test diff"
    prompt = generate_user_prompt(diff)
    assert "test diff" in prompt
    assert "```diff" in prompt

def test_generate_prompt_defaults():
    options = {"type": "conventional", "generate": 2, "locale": "pt"}
    prompt = generate_prompt(options)
    
    assert "exactly 2 conventional style commit messages" in prompt
    # Check if localized example is embedded
    assert "corrigir erro no processo de autentica" in prompt

def test_generate_prompt_gitmoji():
    options = {"type": "gitmoji", "generate": 1, "locale": "en"}
    prompt = generate_prompt(options)
    
    assert "exactly 1 gitmoji style commit message " in prompt
    assert ":sparkles: Add real-time chat feature" in prompt
