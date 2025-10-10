from enum import Enum


class SourceType(Enum):
    """Supported data source types"""

    REST = "rest"
    S3 = "s3"
    FILE = "file"
