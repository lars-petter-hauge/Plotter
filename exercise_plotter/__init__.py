from pkg_resources import get_distribution, DistributionNotFound
from sqlalchemy.orm import sessionmaker

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

# Initiate Session globally on top level
Session = sessionmaker()  # pylint: disable=invalid-name
