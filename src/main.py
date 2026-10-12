import argparse
import json
import sys
import requests
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text

from client import LocalLLMClient, TextChunk, ToolStart, ToolEnd
from config import load_config
from input_prompt import create_prompt_session
from session_manager import SessionManager
from utils.find_session_file import find_session_file

console = Console()

DEFAULT_CONFIG_PATH = "config.toml"
THINKING_LABEL = "[bold green]Thinking..."
MAX_ARGS_DISPLAY = 60

def build_parser(config: dict) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local LLM agent for the command line.")

    parser.add_argument(
        "-c", "--config",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the TOML config file (default: %(default)s)"
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=config["model"]["name"],
        help="Model to use (default: %(default)s)"
    )
    parser.add_argument(
        "-s", "--sys-prompt",
        type=str,
        default=config["model"]["system_prompt"],
        help="Path to the system prompt file (default: %(default)s)"
    )
    parser.add_argument(
        "-u", "--url",
        type=str,
        default=config["model"]["url"],
        help="Ollama API URL (default: %(default)s)"
    )
    parser.add_argument(
        "-i", "--max-iterations",
        type=int,
        default=config["agent"]["max_iterations"],
        help="Maximum number of tool iterations (default: %(default)s)"
    )
    parser.add_argument(
        "--disable-thinking",
        action=argparse.BooleanOptionalAction,
        default=config["model"]["disable_thinking"],
        help="Disable the model's thinking mode (default: %(default)s)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all saved sessions",
    )
    parser.add_argument(
        "--resume",
        nargs="?",
        const="LAST",
        default=None,
        help="Resume a saved session by name or index. Without an argument, resumes the latest session."
    )
    parser.add_argument(
        "--clear",
        type=str,
        help="Delete a session by index or name, or 'all' to delete every session"
    )

    return parser

def format_tool_call(event: ToolStart) -> str:
    """Format a tool call as `name(arg="value")`, truncated when too long."""
    args = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in event.args.items())
    if len(args) > MAX_ARGS_DISPLAY:
        args = args[:MAX_ARGS_DISPLAY - 1] + "…"
    return f"{event.name}({args})"

def wait_next(events, label):
    """Wait for the next event behind a spinner. Returns None at the end of the stream."""
    with console.status(label, spinner="dots"):
        return next(events, None)

def render_response(stream, show_tool_calls: bool):
    """Render the agent's answer: text as Markdown, tool calls as dim lines."""
    events = iter(stream)
    previous = None
    event = wait_next(events, THINKING_LABEL)

    while event is not None:
        if isinstance(event, TextChunk):
            if previous is not None:
                console.print()
            previous = "text"
            text = event.text
            with Live(Markdown(text), console=console, refresh_per_second=15) as live:
                for event in events:
                    if not isinstance(event, TextChunk):
                        break
                    text += event.text
                    live.update(Markdown(text))
                else:
                    event = None
            continue

        if isinstance(event, ToolStart) and show_tool_calls:
            if previous == "text":
                console.print()
            previous = "tool"
            call = format_tool_call(event)
            end = wait_next(events, Text(f"⚙ {call}", style="bold yellow"))
            if isinstance(end, ToolEnd):
                status = ("✓", "green") if end.ok else ("✗", "bold red")
                console.print(Text.assemble(
                    ("  ⚙ ", "dim"), (call, "dim"), "  ", status, (f" {end.duration:.1f}s", "dim")
                ))
            elif end is not None:
                event = end
                continue

        event = wait_next(events, THINKING_LABEL)

def run_chat(client: LocalLLMClient, history_dir: str, show_tool_calls: bool):
    console.print(Panel(
        "\n[bold cyan]Local LLM agent started[/bold cyan]\n"
        "Type [bold red]'quit'[/bold red] or [bold red]'exit'[/bold red] to leave "
        "(or press Ctrl+C twice on an empty input).",
        border_style="cyan"))

    prompt_session = create_prompt_session(model_name=client.model, history_dir=history_dir)

    while True:
        try:
            console.print()
            console.rule(style="dim")
            content = prompt_session.prompt()

            if content.strip().lower() in ["quit", "exit", "/quit", "/exit"]:
                console.print("\n[bold cyan]End of conversation.[/bold cyan]")
                break

            console.print(f"\n[bold blue]Assistant:[/bold blue]\n")

            render_response(client.send_message(content), show_tool_calls)
            print()

        except requests.exceptions.RequestException as e:
            console.print(f"\n[bold red]Network Error: Can't join the API: {e}[/bold red]")
        except  KeyboardInterrupt:
            console.print("\n[bold cyan]End of conversation.[/bold cyan]")
            return

def create_client(args, config: dict) -> LocalLLMClient:
    session_file_to_load = None
    if args.resume:
        session_file_to_load = find_session_file(args.resume, config["paths"]["history_dir"])
        if not session_file_to_load:
            console.print(f"[bold red]No session matches '{args.resume}'[/bold red]")
            sys.exit(1)

    return LocalLLMClient(
        model_name=args.model,
        base_url=args.url,
        sys_prompt_path=args.sys_prompt,
        max_iterations=args.max_iterations,
        disable_thinking=args.disable_thinking,
        session_file=session_file_to_load,
        options=config["model"]["options"],
        tools_config=config["tools"],
        history_dir=config["paths"]["history_dir"]
    )

def load_config_from_args() -> dict:
    """Read only --config, to load the file before building the real parser."""
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("-c", "--config", default=None)
    pre_args, _ = pre_parser.parse_known_args()

    if pre_args.config:
        return load_config(pre_args.config, explicit=True)
    return load_config(DEFAULT_CONFIG_PATH)

def main():
    config = load_config_from_args()
    args = build_parser(config).parse_args()
    history_dir = config["paths"]["history_dir"]

    if args.clear:
        SessionManager.clear(args.clear, history_dir)
        sys.exit(0)

    if args.list:
        SessionManager.list(history_dir)
        sys.exit(0)

    client = create_client(args, config)

    run_chat(client, history_dir, config["display"]["show_tool_calls"])

if __name__ == "__main__":
    main()