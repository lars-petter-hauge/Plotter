from setuptools import setup, find_packages

setup(
    name="exercise_plotter",
    use_scm_version={"write_to": "exercise_plotter/version.py"},
    author="Lars Petter Hauge",
    author_email="larsenhauge@gmail.com",
    url="https://github.com/lars-petter-hauge/exercise_plotter",
    description="Plotter application for plotting training data",
    packages=find_packages(),
    setup_requires=["setuptools_scm"],
    install_requires=[
    ],
)
