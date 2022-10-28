class FileKeyError(Exception):
    """
    Raises when file key does not exists in s3 storage
    """

    pass


class BucketError(Exception):
    """
    Raises when bucket does not exists in s3 storage
    """

    pass


class UploadLimitExceedError(Exception):
    """
    Raises when uploading limit exceeded
    """

    pass


class FileConversionError(Exception):
    """
    Raises when file wasn't converted properly
    """

    pass
