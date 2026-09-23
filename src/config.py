import copy
import sys
import tomllib
from pathlib import Path
from rich.console import Console

console = Console()

# Built-in defaults. config.toml overrides them, CLI flags override config.toml.
DEFAULTS = {
    "model": {
        "name": "qwen3.5:9b",
        "url": "http://localhost:11434/api/chat",
        "system_prompt": "system_prompt.txt",
        "disable_thinking": False,
        # Sent as-is in the Ollama "options" field of every chat request.
        "options": {
            # The qwen3.5:9b Modelfile bakes in presence_penalty=1.5, which is
            # extreme (normal range is ~0-0.5) and actively fights against the
            # model reusing numbers/words already seen earlier in the conversation
            # (like restating a tool result). This caused empty or hallucinated
            # responses in longer tool-calling exchanges.
            "presence_penalty": 0.0,
        },
    },
    "agent": {
        "max_iterations": 15,
    },
    "tools": {
        "request_timeout": 8,
        "fetch_url_max_chars": 5000,
        "read_file_max_kb": 500,
        "search_max_results": 10,
        "search_extract_chars": 1000,
    },
    "paths": {
        "history_dir": "history",
    },
}

# Tables whose keys are free-form (any Ollama option is accepted).
FREE_TABLES = {"model.options"}


def load_config(path: str, explicit: bool = False) -> dict:
    """Charge config.toml et le fusionne avec les valeurs par défaut."""
    config = copy.deepcopy(DEFAULTS)
    config_path = Path(path)

    if not config_path.is_file():
        if explicit:
            console.print(f"[bold red]Error: Config file '{path}' not found.[/bold red]")
            sys.exit(1)
        return config

    try:
        with open(config_path, "rb") as f:
            user_config = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError) as e:
        console.print(f"[bold red]Error: Cannot read config file '{path}': {e}[/bold red]")
        sys.exit(1)

    _merge(config, user_config, prefix="")
    return config


def _merge(base: dict, override: dict, prefix: str):
    """Fusionne récursivement `override` dans `base`, avec des warnings pour les clés invalides."""
    for key, value in override.items():
        full_key = f"{prefix}{key}"

        if prefix.rstrip(".") in FREE_TABLES:
            base[key] = value
            continue

        if key not in base:
            console.print(f"[yellow]Warning: Unknown config key '{full_key}', ignored.[/yellow]")
            continue

        default = base[key]
        if isinstance(default, dict):
            if isinstance(value, dict):
                _merge(default, value, prefix=f"{full_key}.")
            else:
                console.print(f"[yellow]Warning: '{full_key}' must be a table, ignored.[/yellow]")
            continue

        # bool is a subclass of int, so check it explicitly.
        valid = type(value) is type(default) or (
            isinstance(default, float) and type(value) is int
        )
        if not valid:
            console.print(
                f"[yellow]Warning: '{full_key}' must be of type {type(default).__name__}, "
                f"keeping the default ({default!r}).[/yellow]"
            )
            continue

        base[key] = value
