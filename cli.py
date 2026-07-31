import os
import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm

from ai_engine import generate_command_local, generate_command_cloud, is_ollama_available
from utils import execute_command, get_os_info, save_to_history, get_history, clear_history

app = typer.Typer(help="Fast Hybrid AI Terminal Assistant for Developers")
console = Console()

DEFAULT_LOCAL_MODEL = "qwen2:0.5b"

# Friendly labels for display only (the actual tag sent to the AI stays short)
OS_DISPLAY_LABELS = {
    "gitbash": "Git Bash (MINGW64)",
    "powershell": "PowerShell",
    "cmd": "Windows CMD",
    "macos": "macOS",
    "linux": "Linux",
}


def resolve_mode(force_local: bool, force_cloud: bool, model_name: str):
    """
    Decides which backend to use:
      1. If the user explicitly forces one mode (--local / --cloud), respect it.
      2. Otherwise, prefer local Ollama automatically if it's installed and running
         (free, offline, zero API cost).
      3. If Ollama isn't available, fall back to Groq Cloud if an API key is set.
      4. If neither is available, stop and tell the user exactly how to set up either one.
    Returns: (mode: str, api_key: str | None)
    """
    api_key = os.getenv("GROQ_API_KEY")

    if force_local:
        if not is_ollama_available(model_name):
            console.print(f"[bold red]Ollama model '{model_name}' is not available.[/bold red]")
            console.print(f"Run: [yellow]ollama pull {model_name}[/yellow] and make sure Ollama is running.")
            raise typer.Exit(code=1)
        return "local", None

    if force_cloud:
        if not api_key:
            console.print("[bold red]GROQ_API_KEY is not set![/bold red]")
            console.print("Set it via: [yellow]export GROQ_API_KEY='your_key'[/yellow]  (get a free key at https://console.groq.com)")
            raise typer.Exit(code=1)
        return "cloud", api_key

    # Auto mode: prefer local if it's ready to go (free + offline)
    if is_ollama_available(model_name):
        return "local", None

    if api_key:
        return "cloud", api_key

    # Neither is set up — give the user both options clearly
    console.print(Panel(
        "[bold red]No AI backend is available.[/bold red]\n\n"
        "Choose ONE of the following to get started:\n\n"
        f"[bold cyan]Option 1 - Use Groq Cloud (fast, free, needs internet):[/bold cyan]\n"
        f"  1. Get a free API key: [yellow]https://console.groq.com[/yellow]\n"
        f"  2. Run: [yellow]export GROQ_API_KEY='your_key'[/yellow]\n"
        f"  3. Then just run: [green]ai \"your query\"[/green]\n\n"
        f"[bold cyan]Option 2 - Use Ollama (offline, no internet needed):[/bold cyan]\n"
        f"  1. Install Ollama: [yellow]https://ollama.com/download[/yellow]\n"
        f"  2. Pull the model: [yellow]ollama pull {model_name}[/yellow]\n"
        f"  3. Then run: [green]ai \"your query\" --local[/green]",
        title="[bold yellow]Setup Required[/bold yellow]",
        expand=False
    ))
    raise typer.Exit(code=1)


@app.command()
def main(
    prompt: str = typer.Argument(None, help="Natural language query describing what command you want"),
    local: bool = typer.Option(False, "--local", "-l", help="Force local Ollama model (offline)"),
    cloud: bool = typer.Option(False, "--cloud", "-c", help="Force Groq Cloud API"),
    model: str = typer.Option(
        DEFAULT_LOCAL_MODEL, "--model", "-m",
        help="Local Ollama model to use (default is tiny/fast but less reliable; "
             "try qwen2.5-coder:1.5b for better accuracy)"
    ),
    run: bool = typer.Option(False, "--run", "-r", help="Automatically execute command without asking"),
    history: bool = typer.Option(False, "--history", "-H", help="Show past command history"),
    clear: bool = typer.Option(False, "--clear-history", help="Clear past command history")
):
    """
    Generate CLI commands from natural language, or view command history.
    """
    if clear:
        clear_history()
        console.print("[bold green]Command history cleared successfully![/bold green]")
        return

    if history:
        logs = get_history(limit=10)
        if not logs:
            console.print("[yellow]No command history found yet![/yellow]")
            return

        console.print(Panel(
            "".join(logs).strip(),
            title="[bold cyan]Recent Command History[/bold cyan]",
            expand=False
        ))
        return

    if not prompt:
        console.print("[bold red]Error:[/bold red] Please provide a prompt or use [yellow]--history[/yellow] to view past commands.")
        raise typer.Exit(code=1)

    os_info = get_os_info()
    os_display = OS_DISPLAY_LABELS.get(os_info, os_info)
    mode, api_key = resolve_mode(local, cloud, model)
    mode_label = "OFFLINE / OLLAMA" if mode == "local" else "GROQ CLOUD"

    with console.status(f"[bold cyan]AI thinking [{mode_label}] ({os_display})...[/bold cyan]", spinner="dots"):
        try:
            if mode == "local":
                cmd = generate_command_local(prompt, os_info, model_name=model)
            else:
                cmd = generate_command_cloud(prompt, os_info, api_key)
        except Exception as e:
            console.print(f"[bold red]Execution Error:[/bold red] {e}")
            raise typer.Exit(code=1)

    if not cmd:
        console.print("[bold red]The model didn't return a usable command.[/bold red]")
        if mode == "local":
            console.print(
                f"[yellow]Tip:[/yellow] '{model}' may be too small to follow instructions reliably. "
                "Try a larger model, e.g.: [green]ollama pull qwen2.5-coder:1.5b[/green] "
                "then run with [green]--model qwen2.5-coder:1.5b[/green]"
            )
        else:
            console.print("[yellow]Tip:[/yellow] Try rephrasing your request.")
        raise typer.Exit(code=1)

    save_to_history(prompt, cmd)

    console.print(Panel(
        Syntax(cmd, "bash", theme="monokai", word_wrap=True),
        title=f"[bold green]Suggested Command ({os_display}) [{mode_label}][/bold green]",
        subtitle="[dim]Verify command before execution[/dim]",
        expand=False
    ))

    if run:
        should_run = True
    else:
        should_run = Confirm.ask("Do you want to execute this command right now?", default=False)

    if should_run:
        console.print("[bold yellow]Executing command...[/bold yellow]\n")
        execute_command(cmd)


if __name__ == "__main__":
    app()