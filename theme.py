from textual.widgets.text_area import TextAreaTheme
from rich.style import Style

conda_theme = TextAreaTheme(
    name="conda",
    base_style=Style(color="#D4D4D4", bgcolor="#1E1E1E"),
    gutter_style=Style(color="#858585", bgcolor="#1E1E1E"),
    cursor_style=Style(color="#1E1E1E", bgcolor="#4EC9B0"),
    cursor_line_style=Style(bgcolor="#2A2A2A"),
    selection_style=Style(bgcolor="#264F78"),
    syntax_styles={
        "keyword": Style(color="#4EC9B0", bold=True),
        "key": Style(color="#9CDCFE"),
        "value": Style(color="#CE9178"),
        "punctuation": Style(color="#D4D4D4"),
        "string": Style(color="#6A9955"),
        "number": Style(color="#B5CEA8"),
        "boolean": Style(color="#4EC9B0"),
        "null": Style(color="#569CD6"),
        "comment": Style(color="#6A9955", italic=True),
        "function": Style(color="#4EC9B0"),
        "class": Style(color="#4EC9B0"),
        "constant": Style(color="#4FC1FF"),
        "variable": Style(color="#9CDCFE"),
        "property": Style(color="#9CDCFE"),
        "operator": Style(color="#D4D4D4"),
    }
)
