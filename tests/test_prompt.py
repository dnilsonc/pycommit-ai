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

def test_generate_pr_prompt_default():
    from pycommit_ai.prompt import generate_pr_prompt, PR_TEMPLATE
    prompt = generate_pr_prompt("diff", ["commit 1"])
    assert PR_TEMPLATE in prompt

def test_generate_pr_prompt_custom_inline():
    from pycommit_ai.prompt import generate_pr_prompt
    pr_config = {"template": "Custom PR\\n\\nVery custom."}
    prompt = generate_pr_prompt("diff", ["commit 1"], pr_config=pr_config)
    assert "Custom PR\n\nVery custom." in prompt

def test_generate_pr_prompt_custom_path(tmp_path):
    from pycommit_ai.prompt import generate_pr_prompt
    template_file = tmp_path / "pr_template.md"
    template_file.write_text("## PR from File\n\nWorks great!")
    
    pr_config = {"templatePath": str(template_file)}
    prompt = generate_pr_prompt("diff", ["commit 1"], pr_config=pr_config)
    assert "## PR from File\n\nWorks great!" in prompt

def test_generate_pr_prompt_priority(tmp_path):
    from pycommit_ai.prompt import generate_pr_prompt
    template_file = tmp_path / "pr_template.md"
    template_file.write_text("File template")
    
    pr_config = {
        "template": "Inline template",
        "templatePath": str(template_file)
    }
    prompt = generate_pr_prompt("diff", ["commit 1"], pr_config=pr_config)
    assert "Inline template" in prompt
    assert "File template" not in prompt
