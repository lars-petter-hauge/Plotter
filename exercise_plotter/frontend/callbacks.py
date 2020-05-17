import dash
import plotly.graph_objects as go

from exercise_plotter.backend.database_manager import session_scope, DBManager
from exercise_plotter.frontend.util import load_exercise_overview, _get_filter_options
from exercise_plotter.frontend.app import app


data = load_exercise_overview()
_filter_options = _get_filter_options(data)


@app.callback(
    dash.dependencies.Output("crossplot_graph", "figure"),
    [
        dash.dependencies.Input("cp_x_axis_dropdown", "value"),
        dash.dependencies.Input("cp_y_axis_dropdown", "value"),
    ],
)
def update_crossplot(x_axis_value, y_axis_value):
    return {
        "data": [
            go.Scatter(
                x=data[x_axis_value].values,
                y=data[y_axis_value].values,
                mode="markers",
                marker={"size": 10},
            )
        ],
        "layout": go.Layout(
            title="Training Results",
            yaxis={"title": y_axis_value},
            xaxis={"title": x_axis_value},
        ),
    }


filter_input = [
    dash.dependencies.Input("ts_filter_{}".format(option["name"]), "value")
    for option in _filter_options
]


@app.callback(
    dash.dependencies.Output("timeseries_graph", "figure"),
    [
        dash.dependencies.Input("ts_x_axis_dropdown", "value"),
        dash.dependencies.Input("ts_y_axis_dropdown", "value"),
    ]
    + filter_input,
)
def update_timeseriesplot(x_axis_value, y_axis_value, *filters):

    parameters = [option["name"] for option in _filter_options]
    exercise_ids = data["id"].values

    for parameter_name, (minimum, maximum) in zip(parameters, filters):
        exercise_ids = [
            e_id
            for e_id in exercise_ids
            if minimum <= float(data[data["id"] == e_id][parameter_name]) <= maximum
        ]

    timeseries_data = []
    with session_scope() as session:
        db_man = DBManager(session)
        for exercise_id in exercise_ids:
            timeseries_data.append(
                db_man.get_excercise_time_series_values(
                    exercise_id=int(exercise_id),
                    column_names=[x_axis_value, y_axis_value],
                )
            )

    return {
        "data": [
            go.Scatter(
                x=ts_data[x_axis_value].values,
                y=ts_data[y_axis_value].values,
                mode="markers",
                marker={"size": 10},
            )
            for ts_data in timeseries_data
        ],
        "layout": go.Layout(
            title="Training Results",
            yaxis={"title": y_axis_value},
            xaxis={"title": x_axis_value},
        ),
    }
