import logging
from contextlib import contextmanager
from typing import List, Union, Any, Dict

import pandas as pd
from sqlalchemy.schema import UniqueConstraint, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, DateTime

from exercise_plotter import Session

OVERVIEW_TABLE_NAME = "exercises"
TIMESERIES_TABLE_NAME = "exercises_timeseries"

Base = declarative_base()  # type: Any # pylint: disable=C0103


class Exercises(Base):  # pylint: disable=inherit-non-class, too-few-public-methods
    __tablename__ = TIMESERIES_TABLE_NAME

    id = Column(Integer, primary_key=True)

    exercise_id = Column(Integer, ForeignKey("{}.id".format(OVERVIEW_TABLE_NAME)))
    time = Column(Float, nullable=False)

    heart_rate = Column(Integer)
    speed = Column(Float)
    altitude = Column(Float)
    distance = Column(Float)

    __table_args__ = (
        UniqueConstraint("exercise_id", "time", name="_time_unique_constraint_"),
    )

    def __repr__(self):
        return "<exercise_series(id='{}', excercise_id='{}')>".format(
            self.id, self.exercise_id
        )


class ExercisesOverview(
    Base  # pylint: disable=inherit-non-class, bad-continuation
):  # pylint: disable=too-few-public-methods
    __tablename__ = OVERVIEW_TABLE_NAME

    id = Column(Integer, primary_key=True)

    timestamp = Column(DateTime, unique=True, nullable=False)
    duration = Column(Float)
    distance = Column(Float)
    avg_heart_rate = Column(Integer)
    max_heart_rate = Column(Integer)
    avg_speed = Column(Float)
    max_speed = Column(Float)
    calories = Column(Integer)
    fat_percentage_of_calories = Column(Float)
    ascent = Column(Float)
    descent = Column(Float)
    max_altitude = Column(Float)
    running_index = Column(Integer)
    training_load = Column(Integer)
    notes = Column(String)

    exercises = relationship("Exercises")

    def __repr__(self):
        return "<exercise(id='{}', timestamp='{}')>".format(self.id, self.timestamp)


@contextmanager
def session_scope():
    # pylint: disable=no-member
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class DBManager:
    """
    DataBase manager for the Exercise Plotter

    Usage:
        from exercise_plotter.backend.database_manager import DBManager, session_scope

        with session_scope() as session:
            db = DBManager(session)
            db.add_exercise(meta, data)
    """

    def __init__(self, session):
        self.session = session

    def get_excercise_time_series_values(
        self,  # pylint: disable=bad-continuation
        exercise_id: Integer,  # pylint: disable=bad-continuation
        column_names: Union[String, List] = "*",  # pylint: disable=bad-continuation
    ) -> pd.DataFrame:  # pylint: disable=bad-continuation
        """Get the time series for the specified exercise. An overview
        of exercise_ids is given in get_exercise_overview

        Arguments:
            excercise_id {int} -- The id of the exercise

        Keyword Arguments:
            column_names {Union[str, List]} -- column names to provide.
            All will be given by default. (default: {'*'})

        Raises:
            TypeError: column_names must be either a string, or list of strings

        Returns:
            pd.DataFrame -- [description]
        """

        if isinstance(column_names, list):
            column_names = ", ".join(column_names)
        elif not isinstance(column_names, str):
            raise TypeError("column_names must be a string or a list of strings")

        query = (
            self.session.query(Exercises)
            .filter(Exercises.exercise_id == exercise_id)
            .order_by(Exercises.time)
        )

        return pd.read_sql(query.statement, self.session.bind)

    def get_exercise_overview(self) -> pd.DataFrame:
        """Get the available excercises in the database. The function returns
        a pandas DataFrame that, among others, provides the excercise_id for
        each excercise. This can later be used used to retrieve time series
        data with the get_excercise_time_series_values function

        Returns:
            pd.DataFrame -- [description]
        """

        query = self.session.query(ExercisesOverview).order_by(
            ExercisesOverview.timestamp
        )

        return pd.read_sql(query.statement, self.session.bind)

    def add_exercise(self, meta: Dict, data: pd.DataFrame = None) -> Integer:
        """Add an exercise to the database. The metadata should contain single element
        values (such as duration), while data contains the timeseries values. It is required
        to have a timestamp in the metadata, and the value must be unique for every
        exercise added. Trying to add another exercise with the same timestamp will raise
        a KeyError.

        Likewise, the timeseries must contain a time value. The timeseries can be added
        at a later stage with <add_timeseries>.

        Arguments:
            meta {Dict} -- The metadata for an exercise
            data {pd.DataFrame} -- Timeseries values

        Returns:
            Integer -- The exercise_id. This can later be used both to add more
                       time series data and to look up time series data.
        """
        existing_entries = self.session.query(ExercisesOverview).filter(
            ExercisesOverview.timestamp == meta["timestamp"]
        )

        if existing_entries.count() > 0:
            raise AssertionError(
                "An entry at timestamp {} has already been created. "
                "Timestamps must be unique".format(meta["timestamp"])
            )

        try:
            exercise = ExercisesOverview(**meta)
            self.session.add(exercise)
            self.session.commit()

            if data is None:
                return exercise.id

            # Do not modify input dataframe
            data = data.copy()

            data["exercise_id"] = exercise.id

            # if_exists refers only to if a table already exists, which it always should
            # given that the database setup has been completed.
            data.to_sql(
                TIMESERIES_TABLE_NAME,
                self.session.connection(),
                if_exists="append",
                index=False,
            )
            self.session.commit()

        # Currently, this is how we handle a situation where we try to add an
        # excercise that already exists.
        except IntegrityError as err:
            logging.warning(str(err))

        except pd.io.sql.DatabaseError as err:
            logging.warning(str(err))

        return exercise.id

    def add_timeseries(self, exercise_id: Integer, data: pd.DataFrame):
        """Add a timeseries to the given exercise_id. The <time> column
        is required to be in the DataFrame, a KeyError will be raised if
        it is not present.

        It is possible to add parts of the timeseries at one point and add
        the rest later.

        Default value is NaN.

        This function will overwrite existing values by default.

        Arguments:
            exercise_id {Integer} -- The id of the exercise corresponding to the data
            data {pd.DataFrame} -- The timeseries dataframe
        """

        try:
            existing_entries = (
                self.session.query(Exercises)
                .filter(Exercises.exercise_id == exercise_id)
                .order_by(Exercises.time)
                .all()
            )

            existing_times = [o.time for o in existing_entries]

            entries_to_update = data.loc[data["time"].isin(existing_times)]

            for _, entry in entries_to_update.iterrows():
                self.session.query(Exercises).filter(
                    Exercises.exercise_id == exercise_id
                ).filter(Exercises.time == entry.time).update(entry.to_dict())

            remaining_entries = data.loc[~data["time"].isin(existing_times)]

            remaining_entries["exercise_id"] = exercise_id

            # if_exists refers only to if a table already exists, which it always should
            # given that the database setup has been completed.
            remaining_entries.to_sql(
                TIMESERIES_TABLE_NAME,
                self.session.connection(),
                if_exists="append",
                index=False,
            )
            self.session.commit()

        except pd.io.sql.DatabaseError as err:
            logging.warning(str(err))
