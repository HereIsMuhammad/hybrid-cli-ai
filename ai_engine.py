import re
import ollama

# Short, concrete instructions per environment tag (kept SHORT so even
# small local models like qwen2:0.5b can follow them reliably).
OS_INSTRUCTIONS = {
    "gitbash": "Environment: Git Bash on Windows (MINGW64). Use native Linux commands: ls, grep, find, curl, cat, rm, mkdir, etc.",
    "powershell": "Environment: Windows PowerShell. Use PowerShell cmdlets: Get-ChildItem, Get-Process, Remove-Item, etc.",
    "cmd": "Environment: Windows CMD. Use native CMD commands: dir, type, del, copy, etc. If a PowerShell-only cmdlet is required, wrap it as: powershell -Command \"...\"",
    "macos": "Environment: macOS terminal (zsh/bash). Use standard Unix/BSD commands: ls, grep, find, curl, etc.",
    "linux": "Environment: Linux terminal (bash/zsh). Use standard GNU/Linux commands: ls, grep, find, curl, etc.",
}

SYSTEM_PROMPT = """You are a command-line expert. Output ONLY a single raw terminal command. Nothing else.

{os_instruction}

STRICT RULES:
- Output ONLY the command itself. No explanations. No sentences. No headers.
- Never write words like "In", "Use", "Run", "To do this", "Here is", "Note:".
- Never use markdown code fences (no ```).
- Never add a period at the end.

Examples:
User: list files
Command: ls -la

User: show current directory
Command: pwd

User: check disk space
Command: df -h

User: check disk usage
Command: df -h

User: find all python files
Command: find . -name "*.py"

User: show running processes
Command: ps aux

Now respond to the real request with ONLY the command.
"""


def is_ollama_available(model_name: str) -> bool:
    """
    Checks whether the Ollama service is running and whether the
    requested model has been pulled locally. Returns False on any failure.
    """
    try:
        available_models = ollama.list().get("models", [])
        names = [m.get("model", m.get("name", "")) for m in available_models]
        for n in names:
            if n == model_name or n.split(":")[0] == model_name.split(":")[0]:
                return True
        return False
    except Exception:
        return False


def _build_prompt(os_info: str) -> str:
    instruction = OS_INSTRUCTIONS.get(os_info, OS_INSTRUCTIONS["linux"])
    return SYSTEM_PROMPT.format(os_instruction=instruction)


def generate_command_local(prompt: str, os_info: str, model_name: str = "qwen2:0.5b") -> str:
    """Generates a command using a local Ollama model (fully offline)."""
    formatted_prompt = _build_prompt(os_info)
    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": formatted_prompt},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.1}
        )
        cmd = response["message"]["content"].strip()
        return clean_markdown(cmd)
    except Exception as e:
        raise Exception(
            f"Ollama Error: could not reach local model '{model_name}'. "
            f"Make sure the Ollama app/service is running. Details: {e}"
        )


def generate_command_cloud(prompt: str, os_info: str, api_key: str) -> str:
    """Generates a command using Groq's free, fast cloud API."""
    from httpx import post

    formatted_prompt = _build_prompt(os_info)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": formatted_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }

    res = post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=15.0)
    if res.status_code == 200:
        cmd = res.json()["choices"][0]["message"]["content"].strip()
        return clean_markdown(cmd)
    else:
        raise Exception(f"Groq API Error ({res.status_code}): {res.text}")


# Phrases that signal the model wrote an explanation instead of a command.
# Any line starting with these (case-insensitive) gets discarded.
_EXPLANATION_STARTS = (
    "in ", "use ", "run ", "to ", "you ", "here", "note", "this ", "the ",
    "for ", "if ", "since ", "as ", "because ", "so ", "command:", "output:",
    "answer:", "response:", "sure", "certainly", "i ",
)


def clean_markdown(command: str) -> str:
    """
    Strips markdown fences, stray backticks, and any conversational
    filler the model might add, leaving only the raw command.

    Returns an EMPTY STRING if no valid command could be extracted —
    callers must check for this and treat it as a failure, never fall
    back to returning the raw unfiltered text (that's how explanation
    sentences used to get executed as commands).
    """
    command = command.strip()

    # Remove ```bash ... ``` or ``` ... ``` fences
    command = re.sub(r"^```[a-zA-Z]*\n?", "", command)
    command = re.sub(r"\n?```$", "", command)
    command = command.strip()

    lines = [line.strip() for line in command.splitlines() if line.strip()]

    clean_lines = []
    for line in lines:
        stripped = line.strip("`").strip()
        if not stripped:
            continue

        if stripped.startswith("```") or stripped.startswith("#"):
            continue

        # If the line contains a colon, keep only whatever comes AFTER
        # the last colon (handles "Command: ls -la", "Here is the
        # command: ls -la", "In CMD:" with nothing useful, etc.)
        if ":" in stripped:
            after_colon = stripped.rsplit(":", 1)[1].strip()
            if not after_colon:
                # Nothing after the colon -> pure header/explanation, discard
                continue
            stripped = after_colon

        lower = stripped.lower()

        # Still looks like a sentence/explanation -> discard
        if lower.startswith(_EXPLANATION_STARTS):
            continue

        # Strip a single trailing period (models sometimes add one)
        if stripped.endswith(".") and not stripped.endswith(".."):
            stripped = stripped[:-1].strip()

        if stripped:
            clean_lines.append(stripped)

    if clean_lines:
        return clean_lines[0]

    # Nothing survived filtering -> genuinely no valid command was produced
    return ""