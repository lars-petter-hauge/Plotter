import math

import pandas as pd

from exercise_plotter.backend.database_manager import DBManager, session_scope
from sqlalchemy import create_engine
from exercise_plotter import Session

engine = create_engine("sqlite:///example.db")  # pylint: disable=invalid-name
Session.configure(bind=engine)

def load_exercise_overview() -> pd.DataFrame:
    """

    Returns:
        pd.DataFrame -- [description]
    """
    with session_scope() as session:
        db_man = DBManager(session)
        exercise_overview = db_man.get_exercise_overview()

    return exercise_overview


def available_timeseries_parameters():
    """[summary]

    Arguments:
        db_name {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    with session_scope() as session:
        db_man = DBManager(session)
        exercise_overview = db_man.get_exercise_overview()
        timeseries_data = db_man.get_excercise_time_series_values(
            exercise_overview.iloc[0]["id"]
        )

    return timeseries_data.columns


def _get_filter_options(data):
    filter_options = []
    for col in data.columns:
        try:
            filter_options.append(
                {
                    "name": col,
                    "min": int(math.floor(data[col].min())),
                    "max": int(math.ceil(data[col].max())),
                }
            )
            continue
        except TypeError:
            pass

    return filter_options
