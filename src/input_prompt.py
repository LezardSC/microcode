import asyncio
import time
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator, ValidationError

HISTORY_FILE = Path("./history/.input_history")
EXIT_CONFIRM_DELAY = 2.0  # seconds allowed between two Ctrl+C to quit

STYLE = Style.from_dict({
    "prompt": "bold ansicyan",
    "placeholder": "#777777",
    "bottom-toolbar": "noreverse #888888",
    "bottom-toolbar.warning": "noreverse bold ansiyellow",
})


class NonEmptyValidator(Validator):
    def validate(self, document):
        text = document.text.strip()
        if not text:
            raise ValidationError(
                message="Le message ne peut pas être vide",
                cursor_position=0
            )


async def _refresh_after_delay(app):
    await asyncio.sleep(EXIT_CONFIRM_DELAY)
    app.invalidate()


def _setup_key_bindings(state: dict) -> KeyBindings:
    """Configure et retourne les raccourcis clavier pour prompt_toolkit."""
    bindings = KeyBindings()

    @bindings.add('escape', 'enter')
    def _(event):
        event.current_buffer.insert_text('\n')

    @bindings.add('enter')
    def _(event):
        event.current_buffer.validate_and_handle()

    @bindings.add('c-c')
    def _(event):
        buffer = event.current_buffer
        if buffer.text:
            buffer.reset()
            state["last_ctrl_c"] = 0.0
            return

        now = time.monotonic()
        if now - state["last_ctrl_c"] < EXIT_CONFIRM_DELAY:
            event.app.exit(exception=KeyboardInterrupt)
        else:
            state["last_ctrl_c"] = now
            event.app.create_background_task(_refresh_after_delay(event.app))

    @bindings.add('c-d')
    def _(event):
        buffer = event.current_buffer
        if buffer.text:
            buffer.delete()
        else:
            event.app.exit(exception=KeyboardInterrupt)

    @bindings.add('c-z')
    def _(event):
        event.current_buffer.undo()

    return bindings


def create_prompt_session(model_name: str) -> PromptSession:
    """Crée la zone de saisie : multiligne, historique persistant et barre d'aide."""
    state = {"last_ctrl_c": 0.0}

    def bottom_toolbar():
        if time.monotonic() - state["last_ctrl_c"] < EXIT_CONFIRM_DELAY:
            return HTML("<warning>  Appuyez à nouveau sur Ctrl+C pour quitter</warning>")
        return HTML(
            f"  Entrée envoyer · Alt+Entrée nouvelle ligne · Ctrl+C effacer · {model_name}"
        )

    HISTORY_FILE.parent.mkdir(exist_ok=True)

    return PromptSession(
        message=[("class:prompt", "> ")],
        prompt_continuation="  ",
        placeholder=[("class:placeholder", "Écrivez votre message…")],
        bottom_toolbar=bottom_toolbar,
        style=STYLE,
        key_bindings=_setup_key_bindings(state),
        history=FileHistory(str(HISTORY_FILE)),
        validator=NonEmptyValidator(),
        validate_while_typing=False,
        multiline=True,
    )
