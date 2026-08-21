<div align="center">

# 🖥️ Hybrid CLI AI

### Turn plain language into the exact terminal command you need, automatically using Groq Cloud or a fully offline Ollama model.

![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/Groq-Cloud%20API-F55036?style=for-the-badge)](https://groq.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Offline%20Mode-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com/)
[![Typer](https://img.shields.io/badge/Typer-CLI-2E7D32?style=for-the-badge)](https://typer.tiangolo.com/)
[![Rich](https://img.shields.io/badge/Rich-Terminal%20UI-9C27B0?style=for-the-badge)](https://github.com/Textualize/rich)

[![Windows](https://img.shields.io/badge/Windows-Git%20Bash%20%2F%20CMD%20%2F%20PowerShell-0078D6?style=for-the-badge&logo=windows&logoColor=white)]()
[![Linux](https://img.shields.io/badge/Linux-Supported-FCC624?style=for-the-badge&logo=linux&logoColor=black)]()
[![macOS](https://img.shields.io/badge/macOS-Supported-000000?style=for-the-badge&logo=apple&logoColor=white)]()
[![Version](https://img.shields.io/badge/Version-0.1.0-blue?style=for-the-badge)]()

</div>

Turn plain language into the exact terminal command you need automatically using **Groq Cloud** (fast, free) when available, or falling back to a fully **offline Ollama model** when it's not.

No need to remember flags or syntax for `ls`, `Get-ChildItem`, `findstr`, `grep`, or anything else, just describe what you want, in whatever language feels natural.

## ✨ Features

- 🧠 **Smart Auto Mode**: automatically prefers a locally running Ollama model (free, offline) if available, otherwise falls back to Groq Cloud
- 🌐 **Cloud Mode (`--cloud`)**: force Groq's fast, free API (`llama-3.3-70b-versatile`)
- 📴 **Offline Mode (`--local`)**: force a local Ollama model, zero internet required
- 🗣️ **Multilingual Prompts**: write your request in English, Urdu, Hindi, Roman Urdu, or mixed language; the model understands intent, not just keywords
- 🔍 **Precise Shell Detection**: tells the AI exactly whether it's talking to Git Bash, PowerShell, CMD, macOS, or Linux, so commands are actually correct for that shell
- 🧹 **Robust Output Cleaning**: strips markdown fences and filters out explanatory sentences, so only a real command is ever returned (never runs raw AI chatter as a command)
- ⚡ **Auto-Run Option**: skip the confirmation prompt and execute immediately (`--run`)
- 📜 **Command History**: every generated command is logged locally; view or clear it anytime
- 🎨 **Clean Terminal UI**: syntax-highlighted, readable output via Rich

## 📦 Installation

```bash
git clone https://github.com/HereIsMuhammad/hybrid-cli-ai.git
cd hybrid-cli-ai
pip install -e .
```

## 🔑 Setup: Groq API Key (Cloud Mode)

1. Get a free API key from the [Groq Console](https://console.groq.com/)
2. Set it as an environment variable:

```bash
export GROQ_API_KEY="your_key_here"        # Linux / macOS
setx GROQ_API_KEY "your_key_here"          # Windows CMD
$env:GROQ_API_KEY="your_key_here"          # PowerShell
```

> ⚠️ Never hardcode your API key in the code, and never commit it to GitHub.

## 📴 Offline Mode Setup (Ollama)

Install [Ollama](https://ollama.com/download) to enable `--local` / auto-offline mode.

**Windows (PowerShell):**
```powershell
irm https://ollama.com/install.ps1 | iex
```
Or download the [installer directly](https://ollama.com/download/windows) (requires Windows 10+).

**macOS:**
[Download for macOS](https://ollama.com/download/mac)

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Then pull a model. The default is a tiny, very fast model:
```bash
ollama pull qwen2:0.5b
```

For more reliable, accurate command generation (recommended if you have the disk space), use a larger code-tuned model instead:
```bash
ollama pull qwen2.5-coder:1.5b
```
```bash
ai "your query" --local --model qwen2.5-coder:1.5b
```

> Small models like `qwen2:0.5b` are fast and lightweight but occasionally struggle to follow instructions strictly. If you see "The model didn't return a usable command," try a larger model.

## 🚀 Usage

```bash
# Auto mode: uses local Ollama if it's running, otherwise falls back to Groq Cloud
ai "list all files modified today"

# Force Groq Cloud explicitly
ai "kill process running on port 3000" --cloud

# Force fully offline Ollama
ai "find all .log files larger than 100MB" --local

# Use a specific local model
ai "compress this folder into zip" --local --model qwen2.5-coder:1.5b

# Skip confirmation and execute immediately
ai "clear npm cache" --run

# View past command history
ai --history

# Clear command history
ai --clear-history
```

### 🗣️ Multilingual Example

You don't have to phrase requests in perfect English. Roman Urdu, Urdu script, Hindi, or mixed language all work, since the underlying model (Groq's Llama 3.3, or your local Ollama model) understands natural language, not fixed keywords:

```bash
$ ai "disk space dekho kitni h" --cloud
╭─ Suggested Command (Git Bash (MINGW64)) [GROQ CLOUD] ─╮
│ df -h                                                 │
╰─────────── Verify command before execution ───────────╯
Do you want to execute this command right now? [y/n] (n): y
Executing command...
Filesystem            Size  Used Avail Use% Mounted on
C:/Program Files/Git  100G   96G  4.3G  96% /
D:                    124G  2.2G  122G   2% /d
```

> **Note:** Cloud mode (Groq's larger model) handles mixed-language and Roman Urdu prompts noticeably better than small local models. If you're using `--local` with a tiny model like `qwen2:0.5b`, stick closer to plain English for best results; bigger local models (e.g. `qwen2.5-coder:1.5b` or larger) handle multilingual prompts more reliably too.

## ⚙️ How It Works

```
Prompt → Shell Detection (Git Bash / PowerShell / CMD / macOS / Linux)
       → Backend Selection (Ollama if available → else Groq Cloud)
       → AI generates raw command
       → Output cleaned (fences & explanations stripped)
       → Preview shown → Execute (optional)
```

- If neither Ollama nor a `GROQ_API_KEY` is set up, the tool shows clear setup instructions for both options instead of failing silently.
- Output cleaning is strict: if the model returns an explanation instead of a command, the tool reports failure rather than risk running the wrong thing.

## 🛡️ Safety Note

This tool can execute AI-generated shell commands directly (with `--run` or after confirmation). Always review the suggested command before running it, especially for destructive operations like delete, format, or killing processes. Avoid `--run` with vague or ambiguous prompts.

## 🤝 Contributing

PRs and issues are welcome! Open a GitHub Issue for bugs or feature requests.

## 📄 License

MIT License, see [LICENSE](LICENSE) for details.

<div align="center">

### ⭐ If this repo helped you, consider giving it a star!

</div>
