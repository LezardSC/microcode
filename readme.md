# Minicode - Local Autonomous Agent (Ollama & Python)

Minicode (a reference to Opencode) is an autonomous LLM agent developed from scratch in Python.
The goal of this project is to deeply understand how AI agents work (Tool Calling, ReAct loop, memory) by building everything "from scratch" before eventually moving on to heavier frameworks (LangGraph, CrewAI). The project relies on the local **Ollama** API (ideally with a model that is good at tool calling, such as Qwen 2.5 / 3.5).

I'm making it public because I tried to make it modular enough for someone else to use, and as the roadmap progresses, this agent should be able to provide assistance to people who need a small agent for simple tasks without having to pay for or burn tokens on other services.

## Current Features

* **Direct API communication**: Raw HTTP calls to the local Ollama API.
* **Tool introspection**: Dynamic generation of tool JSON schemas (the LLM automatically understands the available Python functions through their *docstrings*).
* **Autonomous ReAct loop**: The agent is able to chain multiple tool calls autonomously until the task is resolved.
* **Built-in tools**:

  * `search_web`: Quick internet search via DuckDuckGo.
  * `fetch_url`: Scraping and full cleaning of a web page (BeautifulSoup).
  * `read_file`: Secure reading of local files.
  * `calculate`: Mathematical calculations.
  * `get_weather`: Fetching the weather for a given city or region.
  * `search_wikipedia`: Searching Wikipedia for a given topic or concept.
  * `get_time`: Tool allowing the agent to know the current time based on the system clock.

## 🚀 Installation

1. **Prerequisites**: Make sure [Ollama](https://ollama.com/) is installed and running on your machine with a compatible model (e.g. `qwen2.5:14b` or `qwen3.5:9b`).

   ```bash
   ollama pull qwen2.5:14b
   ```
2. **Clone the repository**:

   ```bash
   git clone [https://github.com/lezardsc/minicode.git](https://github.com/lezardsc/minicode.git)
   cd minicode
   ```
3. **Install the dependencies**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

Simply run the main script to interact with the agent from your terminal:
`bash
    python3 main.py
    `

## ROADMAP

This project is being developed iteratively. Here are the approximate development stages:

### Phase 1 - Foundations

* Raw HTTP call to Ollama ✅
* Client-side conversation history management ✅
* Tool calling with a single tool ✅
* Multi-tool support with parameters + dynamic schema generation through introspection ✅

### Phase 2 - The Autonomous Agent

* System prompt ✅
* ReAct loop: chaining multiple tool calls until the final answer ✅
* Deeper Internet search ✅
* Mastering thinking mode: understanding, using, or disabling Qwen3.5's `<think>` mode ✅
* Arguments to disable thinking mode ✅

### Phase 2.5 - User Experience

* Arguments to load a model, a system prompt, a URL, and a maximum number of iterations ✅
* Response streaming: displaying tokens as they are generated ✅
* Better input
* Markdown rendering and colors
* `config.toml` for loading default configurations

### Phase 3 - Level Up

* Conversation persistence ✅
* Managing growing context: truncating, summarizing, or archiving old turns to avoid exceeding the context window
* Long-term memory with embeddings
* Code execution tool
* Multimodality - images
* Audio (speech-to-text)
* Migration to the OpenAI SDK

### Phase 4 - Agent Framework

* Exploring a framework (between LangGraph, CrewAI, or smolagents)
* Reimplementing my current agent with the framework
* Comparing them

### Phase 5 - Multi-Agent Systems

* First two-agent system
* Hierarchical pattern (supervisor/worker)
* Debate/consensus pattern
* Parallel pattern
* Structured communication
* Personal mini-project to test it

### Phase 6 - Advanced Topics

* MCP
* Observability and logging
* Agent evaluation
* Robustness and guardrails
* Case study: OpenCode source code
* Cost and optimization
* Video
* Sandboxed code execution, with a tool that executes code in an isolated environment.

### Phase 7 - Application Projects

* Documentation agent: takes a repo, goes through it, and generates a README or documentation for each module.
* Test runner agent: analyzes code, generates tests, runs them, and iterates on failures.
* Refactoring agent: refactors code while explaining each change in a comment/sidecar file.
* Code translation agent: Python -> Rust, JS -> Go, etc.

This project is for educational purposes. Feel free to open an issue or submit a PR if you'd like to discuss the architecture!
