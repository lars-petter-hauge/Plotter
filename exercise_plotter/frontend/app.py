import dash  # type: ignore

_EXT_STYLE = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(
    __name__, external_stylesheets=_EXT_STYLE, suppress_callback_exceptions=True
)

server = app.server  # Necessary for the debug session in vscode
