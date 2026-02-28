import concurrent.futures
from typing import Iterator, List, Tuple

from pycommit_ai.errors import AIServiceError, KnownError
from pycommit_ai.git import GitDiff
from pycommit_ai.prompt import generate_pr_prompt
from pycommit_ai.services import AIResponse, AIService


def generate_commits_parallel(services: List[AIService]) -> Iterator[Tuple[str, str, List[AIResponse] | str]]:
    """
    Executes commit generation across multiple AI services in parallel.
    Yields tuples of (status, service_name, data_or_error) as they complete.
    Status can be 'success' or 'error'.
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_service = {
            executor.submit(srv.generate_commit_messages): f"{srv.__class__.__name__.replace('Service', '')} ({srv.model_name})"
            for srv in services
        }
        
        for future in concurrent.futures.as_completed(future_to_service):
            srv_name = future_to_service[future]
            try:
                results = future.result()
                yield "success", srv_name, results
            except AIServiceError as e:
                yield "error", srv_name, str(e)
            except Exception as e:
                yield "error", srv_name, f"Unexpected error: {str(e)}"


def generate_pr_description(config: dict, branch: str, diff: GitDiff, commits: List[str], locale: str = "en") -> str:
    """
    Generates a PR description using the configured Gemini service.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise KnownError("Google GenAI SDK is required for PR generation.")

    # Find API key — use first available provider
    api_key = config.get("GEMINI", {}).get("key")
    model = config.get("GEMINI", {}).get("model", ["gemini-2.5-flash"])[0]

    if not api_key:
        raise KnownError("PR generation requires a Gemini API key. Run 'pycommit-ai config set GEMINI.key=YOUR_KEY'")

    prompt = generate_pr_prompt(diff.diff, commits, locale)

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=2048,
        ),
    )

    if not response.text:
        raise KnownError("Empty response from AI.")

    pr_text = response.text.strip()
    # Remove markdown fences if the AI wraps it
    if pr_text.startswith("```"):
        lines = pr_text.split("\n")
        pr_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    return pr_text
