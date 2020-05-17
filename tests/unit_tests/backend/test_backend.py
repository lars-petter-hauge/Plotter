import datetime
import pandas as pd
import pytest
from sqlalchemy import create_engine

from exercise_plotter import Session
from exercise_plotter.backend.database_manager import (
    OVERVIEW_TABLE_NAME,
    TIMESERIES_TABLE_NAME,
    Base,
    DBManager,
    session_scope,
)

# Pyling does not conform well with how pytest want us to setup fixtures
# Disable the redifining outer name in order for us to use fixtures
# pylint: disable=redefined-outer-name

# We create an in memory database for the tests
engine = create_engine("sqlite:///test")  # pylint: disable=invalid-name
Session.configure(bind=engine)

DUMMY_META_ONE = {
    "timestamp": datetime.datetime(2000, 1, 1, 12, 0, 0),
    "duration": 12.34,
    "distance": 11.22,
    "avg_heart_rate": 120,
    "max_heart_rate": 125,
    "avg_speed": 3.45,
    "max_speed": 2.34,
    "calories": 123,
    "fat_percentage_of_calories": 0.23,
    "running_index": 41,
    "training_load": 42,
    "ascent": 501,
    "descent": 502,
    "max_altitude": 503,
    "notes": "Something to write",
}

DUMMY_DATA_ONE = pd.DataFrame.from_dict(
    {
        "time": [0, 1, 2, 3, 4],
        "heart_rate": [120, 121, 122, 123, 124],
        "speed": [5.5, 4.5, 4.0, 3.5, 3.0],
        "altitude": [30, 31, 32, 31, 30],
        "distance": [11, 12, 13, 14, 15],
    }
)

DUMMY_NOTE = """
Something else entirely, but perhaps a slightly bigger note.
We would like to verify that it is possible to add some mumbo jumbo about how easy the trip was,
or how nice it was to feel the air in the breeze
"""

DUMMY_META_TWO = {
    "timestamp": datetime.datetime(2000, 1, 2, 12, 0, 0),
    "duration": 22.34,
    "distance": 21.22,
    "avg_heart_rate": 220,
    "max_heart_rate": 225,
    "avg_speed": 4.45,
    "max_speed": 5.34,
    "calories": 223,
    "fat_percentage_of_calories": 0.24,
    "running_index": 51,
    "training_load": 52,
    "ascent": 601,
    "descent": 602,
    "max_altitude": 603,
    "notes": DUMMY_NOTE,
}

DUMMY_DATA_TWO = pd.DataFrame.from_dict(
    {
        "time": [0, 0.1, 0.2, 0.3, 0.4],
        "heart_rate": [90, 91, 92, 91, 90],
        "speed": [5.1, 5.2, 5.3, 5.4, 5.5],
        "altitude": [30.1, 21.3, 42.5, 51, 41],
        "distance": [1.1, 1.2, 1.3, 1.4, 1.5],
    }
)


def _assert_db_content(overview_results=None, timeseries_results=None):

    if overview_results is not None:
        # Verify exercise overview
        result = pd.read_sql(OVERVIEW_TABLE_NAME, engine)
        result = result.drop("id", axis=1)

        if isinstance(overview_results, dict):
            overview_results = pd.DataFrame(overview_results, index=[0])

        assert set(result.columns) == set(overview_results.columns)
        # reorder columns
        expected_result = overview_results[result.columns]

        pd.testing.assert_frame_equal(result, expected_result, check_dtype=False)

    if timeseries_results is not None:
        # Verify time series
        result = pd.read_sql(TIMESERIES_TABLE_NAME, engine)
        result = result.drop(["id", "exercise_id"], axis=1)

        assert set(result.columns) == set(timeseries_results.columns)
        # reorder columns
        expected_result = timeseries_results[result.columns]

        pd.testing.assert_frame_equal(result, expected_result, check_dtype=False)


@pytest.fixture()
def db_manager():
    # Make sure we have a clean database
    Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)
    with session_scope() as session:
        yield DBManager(session)

    # check if error fails, if session closes,
    # the tear down won't work. Might need to be checked for

    # Cleanup
    Base.metadata.drop_all(engine)


def test_add_exercise_full(db_manager):
    db_manager.add_exercise(meta=DUMMY_META_ONE)

    _assert_db_content(overview_results=DUMMY_META_ONE)


def test_add_exercise_full_and_data(db_manager):
    db_manager.add_exercise(meta=DUMMY_META_ONE, data=DUMMY_DATA_ONE)

    _assert_db_content(
        overview_results=DUMMY_META_ONE, timeseries_results=DUMMY_DATA_ONE
    )


def test_add_timeseries_empty_exercise(db_manager):
    exercise_id = db_manager.add_exercise(meta=DUMMY_META_ONE)
    db_manager.add_timeseries(exercise_id=exercise_id, data=DUMMY_DATA_ONE)

    _assert_db_content(
        overview_results=DUMMY_META_ONE, timeseries_results=DUMMY_DATA_ONE
    )


def test_add_timeseries_existing_values(db_manager):
    required_column = DUMMY_DATA_ONE[["time"]]
    data = DUMMY_DATA_ONE.drop("time", axis=1)

    existing_columns = data.columns

    first_batch = pd.concat([required_column, data[existing_columns[:2]]], axis=1)
    second_batch = pd.concat([required_column, data[existing_columns[2:]]], axis=1)

    # Start by adding some of the columns
    exercise_id = db_manager.add_exercise(meta=DUMMY_META_ONE, data=first_batch)

    # Add the remaining ones
    db_manager.add_timeseries(exercise_id=exercise_id, data=second_batch)

    _assert_db_content(
        overview_results=DUMMY_META_ONE, timeseries_results=DUMMY_DATA_ONE
    )


def test_add_timeseries_different_timevalues(db_manager):
    # We want to verify that our database behaves if a user
    # Adds multiple timeseries that does not have consistent time values
    # e.g. <heart_rate> is measured at time 0,2,4 - while <distance> is measured
    # at time 0,1,2,3,4
    required_column = DUMMY_DATA_ONE[["time"]]
    data = DUMMY_DATA_ONE.drop("time", axis=1)

    existing_columns = data.columns

    first_batch = pd.concat([required_column, data[existing_columns[:2]]], axis=1)

    # Adding a shift in the time values
    second_batch = pd.concat([required_column + 2, data[existing_columns[2:]]], axis=1)

    exercise_id = db_manager.add_exercise(meta=DUMMY_META_ONE, data=first_batch)

    db_manager.add_timeseries(exercise_id=exercise_id, data=second_batch)

    expected_results = pd.merge(first_batch, second_batch, how="outer", on="time")

    _assert_db_content(
        overview_results=DUMMY_META_ONE, timeseries_results=expected_results
    )


def test_append_timeseries(db_manager):
    # Start by adding some of the rows
    exercise_id = db_manager.add_exercise(meta=DUMMY_META_ONE, data=DUMMY_DATA_ONE[:3])

    # Add the remaining ones
    db_manager.add_timeseries(exercise_id=exercise_id, data=DUMMY_DATA_ONE[3:])

    _assert_db_content(
        overview_results=DUMMY_META_ONE, timeseries_results=DUMMY_DATA_ONE
    )


def test_duplicate_exercise_not_allowed(db_manager):
    db_manager.add_exercise(meta=DUMMY_META_ONE)

    with pytest.raises(AssertionError):
        db_manager.add_exercise(meta=DUMMY_META_ONE)


def test_duplicate_time_series_is_ok(db_manager):
    exercise_id = db_manager.add_exercise(meta=DUMMY_META_ONE)
    db_manager.add_timeseries(exercise_id=exercise_id, data=DUMMY_DATA_ONE)

    _assert_db_content(
        overview_results=DUMMY_META_ONE, timeseries_results=DUMMY_DATA_ONE
    )

    # Add the same timeseries again. This will update all entries,
    # but should be perfectly valid.
    db_manager.add_timeseries(exercise_id=exercise_id, data=DUMMY_DATA_ONE)

    _assert_db_content(
        overview_results=DUMMY_META_ONE, timeseries_results=DUMMY_DATA_ONE
    )


def test_update_time_series(db_manager):
    exercise_id = db_manager.add_exercise(meta=DUMMY_META_ONE)
    db_manager.add_timeseries(exercise_id=exercise_id, data=DUMMY_DATA_ONE)

    _assert_db_content(
        overview_results=DUMMY_META_ONE, timeseries_results=DUMMY_DATA_ONE
    )

    # Add modified version with same time values - verify updated results
    modified_dummy_data = DUMMY_DATA_ONE.copy()
    modified_dummy_data["heart_rate"][0] = DUMMY_DATA_ONE["heart_rate"][0] - 10

    db_manager.add_timeseries(exercise_id=exercise_id, data=modified_dummy_data)

    _assert_db_content(
        overview_results=DUMMY_META_ONE, timeseries_results=modified_dummy_data
    )


def test_timestamp_in_exercise_must_exist(db_manager):
    data = DUMMY_META_ONE.copy()
    data.pop("timestamp")

    # KeyError is default exception for the pandas to_sql, when a column is required
    with pytest.raises(KeyError):
        db_manager.add_exercise(meta=data)


def test_time_in_timeseries_must_exist(db_manager):
    exercise_id = db_manager.add_exercise(meta=DUMMY_META_ONE)
    data = DUMMY_DATA_ONE.drop("time", axis=1)

    # KeyError is default exception for the pandas to_sql, when a column is required
    with pytest.raises(KeyError):
        db_manager.add_timeseries(exercise_id=exercise_id, data=data)


def test_add_multiple_exercises(db_manager):
    db_manager.add_exercise(meta=DUMMY_META_ONE, data=DUMMY_DATA_ONE)
    db_manager.add_exercise(meta=DUMMY_META_TWO, data=DUMMY_DATA_TWO)

    expected_results = (
        pd.concat([DUMMY_DATA_ONE, DUMMY_DATA_TWO], axis=0)
        .reset_index()
        .drop("index", axis=1)
    )

    # Not sure if this is the most sound way of doing it..
    expected_overview = {k: [v, DUMMY_META_TWO[k]] for k, v in DUMMY_META_ONE.items()}

    expected_overview = pd.DataFrame(expected_overview)

    _assert_db_content(
        overview_results=expected_overview, timeseries_results=expected_results,
    )


def test_get_exercise_overview(db_manager):
    db_manager.add_exercise(meta=DUMMY_META_ONE, data=DUMMY_DATA_ONE)
    db_manager.add_exercise(meta=DUMMY_META_TWO, data=DUMMY_DATA_TWO)

    results = db_manager.get_exercise_overview()

    expected_dummy_one = pd.Series(DUMMY_META_ONE)
    results_one = results.iloc[0].drop("id").reindex(index=expected_dummy_one.index)
    results_one = results_one.rename(
        None
    )  # The name is the given exercise ID - not interested in that
    pd.testing.assert_series_equal(results_one, expected_dummy_one)

    expected_dummy_two = pd.Series(DUMMY_META_TWO)
    results_two = results.iloc[1].drop("id").reindex(index=expected_dummy_two.index)
    results_two = results_two.rename(None)
    pd.testing.assert_series_equal(results_two, expected_dummy_two)


def test_get_excercise_time_series_values(db_manager):
    exercise_id = db_manager.add_exercise(meta=DUMMY_META_ONE, data=DUMMY_DATA_ONE)

    results = db_manager.get_excercise_time_series_values(exercise_id=exercise_id)
    results = results.drop(["id", "exercise_id"], axis=1)
    pd.testing.assert_frame_equal(results, DUMMY_DATA_ONE, check_dtype=False)
