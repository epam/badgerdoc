class FileKeyError(Exception):
    """
    Raises when file key does not exists in s3 storage
    """


class BucketError(Exception):
    """
    Raises when bucket does not exists in s3 storage
    """


class UploadLimitExceedError(Exception):
    """
    Raises whe uploading limit exceeded
    """
