from itertools import chain

import dash_core_components as dcc  # type: ignore
import dash_html_components as html  # type: ignore


def sidebar_layout(id_prefix, axis_options, filter_options=None):
    sidebar = [
        dcc.Dropdown(
            id="{}_y_axis_dropdown".format(id_prefix),
            options=[{"label": col, "value": col} for col in axis_options],
            value=axis_options[0],
        ),
        dcc.Dropdown(
            id="{}_x_axis_dropdown".format(id_prefix),
            options=[{"label": col, "value": col} for col in axis_options],
            value=axis_options[0],
        ),
    ]

    if filter_options:
        labels = [
            html.Label(children=option["name"], style={"padding-bottom": "2.5em",},)
            for option in filter_options
        ]
        rangesliders = [
            dcc.RangeSlider(
                id="{}_filter_{}".format(id_prefix, option["name"]),
                min=option["min"],
                max=option["max"],
                allowCross=False,
                value=[option["min"], option["max"]],
                marks={
                    option["min"]: str(option["min"]),
                    option["max"]: str(option["max"]),
                },
                tooltip={"always_visible": True},
            )
            for option in filter_options
        ]

        flattened = chain.from_iterable(zip(labels, rangesliders))
        sidebar.extend(flattened)

    return sidebar


def crossplot_layout(axis_options):
    return html.Div(
        children=[
            html.H2(children="Crossplot"),
            html.Div(
                children="""
                        Interactive plotting tool for exercise data
                    """
            ),
            html.Div(
                [
                    html.Div(
                        sidebar_layout(id_prefix="cp", axis_options=axis_options,),
                        className="three columns",
                    ),
                    html.Div(
                        [dcc.Graph(id="crossplot_graph")], className="nine columns"
                    ),
                ],
                className="row",
            ),
        ]
    )


def timeseries_layout(axis_options, filter_options):
    return html.Div(
        children=[
            html.H2(children="Timeseries"),
            html.Div(
                children="""
                        Interactive plotting tool for exercise data
                    """
            ),
            html.Div(
                [
                    html.Div(
                        sidebar_layout(
                            id_prefix="ts",
                            axis_options=axis_options,
                            filter_options=filter_options,
                        ),
                        className="three columns",
                        style={"text-align": "center"},
                    ),
                    html.Div(
                        [dcc.Graph(id="timeseries_graph")], className="nine columns"
                    ),
                ],
                className="row",
            ),
        ]
    )
