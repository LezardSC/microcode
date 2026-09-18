import re

# rich.markdown.Markdown only understands standard Markdown, not LaTeX.
# Local models sometimes still emit LaTeX math notation (e.g. \mathbf{90}),
# which would otherwise show up as raw, unrendered LaTeX in the terminal.
_REPLACEMENTS = [
    (re.compile(r"\\mathbf\{([^{}]*)\}"), r"**\1**"),
    (re.compile(r"\\textbf\{([^{}]*)\}"), r"**\1**"),
    (re.compile(r"\\mathit\{([^{}]*)\}"), r"*\1*"),
    (re.compile(r"\\text\{([^{}]*)\}"), r"\1"),
    (re.compile(r"\\frac\{([^{}]*)\}\{([^{}]*)\}"), r"(\1/\2)"),
    (re.compile(r"\\sqrt\{([^{}]*)\}"), r"√(\1)"),
    (re.compile(r"\\times"), "×"),
    (re.compile(r"\\cdot"), "·"),
    (re.compile(r"\\div"), "÷"),
    (re.compile(r"\\pm"), "±"),
    (re.compile(r"\\leq"), "≤"),
    (re.compile(r"\\geq"), "≥"),
    (re.compile(r"\\neq"), "≠"),
    (re.compile(r"\\approx"), "≈"),
    (re.compile(r"\\infty"), "∞"),
    (re.compile(r"\\pi\b"), "π"),
    # Delimiters: keep the content, drop the LaTeX wrapper.
    (re.compile(r"\\\[(.*?)\\\]", re.DOTALL), r"\1"),
    (re.compile(r"\\\((.*?)\\\)", re.DOTALL), r"\1"),
    (re.compile(r"\${1,2}([^$]*?)\${1,2}"), r"\1"),
]


def sanitize_latex(text: str) -> str:
    """Convert common LaTeX math notation to plain/Markdown text.

    Local models sometimes wrap results in LaTeX (\\mathbf{90}, \\frac{1}{2}, ...)
    even though only Markdown is rendered, which leaks raw LaTeX into the output.
    """
    for pattern, replacement in _REPLACEMENTS:
        text = pattern.sub(replacement, text)
    return text
