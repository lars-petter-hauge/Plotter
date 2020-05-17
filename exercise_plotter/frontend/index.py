import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from sqlalchemy import create_engine

from exercise_plotter.frontend.app import app
from exercise_plotter.frontend.layouts import crossplot_layout, timeseries_layout
from exercise_plotter.frontend.util import (
    load_exercise_overview,
    available_timeseries_parameters,
    _get_filter_options,
)
from exercise_plotter import Session
# Required import of callbacks, even though it is not explicitly used in this file
import exercise_plotter.frontend.callbacks  # pylint: disable=unused-import

engine = create_engine("sqlite:///example.db")  # pylint: disable=invalid-name
Session.configure(bind=engine)

data = load_exercise_overview()
ts_parameters = available_timeseries_parameters()
_filter_options = _get_filter_options(data)

app.layout = html.Div(
    [
        html.H1(children="Exercise Plotter"),
        dcc.Tabs(
            id="tabs_selection",
            value="crossplot",
            children=[
                dcc.Tab(label="Crossplot", value="crossplot"),
                dcc.Tab(label="Timeseries", value="timeseries"),
            ],
        ),
        html.Div(id="tabs_content"),
    ]
)


@app.callback(Output("tabs_content", "children"), [Input("tabs_selection", "value")])
def render_content(tab):
    if tab == "crossplot":
        return crossplot_layout(data.columns)
    if tab == "timeseries":
        return timeseries_layout(
            axis_options=ts_parameters, filter_options=_filter_options
        )

    raise NotImplementedError


if __name__ == "__main__":
    app.run_server(debug=True)
