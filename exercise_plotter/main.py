import argparse
import os
import yaml
from typing import Dict
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from exercise_plotter import Session
from exercise_plotter.frontend.plotter import entry_point
from exercise_plotter.backend.database_manager import Base


def valid_session_class(path: str):
    # TODO: test that the db exists (and working), if not create a new from default path
    engine = create_engine("sqlite:///{}".format(path))
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def valid_config(filename: str) -> Dict:
    """Load configuration from a yaml file"""
    with open(filename) as f:
        return yaml.safe_load(f)


def existing_dir(dir_name: str) -> str:
    if not os.path.isdir(dir_name):
        raise argparse.ArgumentTypeError(
            "The given path <{}> is not a directory".format(dir_name)
        )
    return dir_name


def build_parser() -> argparse.ArgumentParser:
    description = """
The Exercise Plotter provides plotting for exercise data
and especially comparing multiple training sessions together
"""
    parser = argparse.ArgumentParser(description)

    parser.add_argument(
        "--path",
        "-p",
        type=valid_session_class,
        help="Path to database",
        required=False,
    )

    return parser


def main_entry():
    parser = build_parser()
    args = parser.parse_args()

    entry_point(args.path)
