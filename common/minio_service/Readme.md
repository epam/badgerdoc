Installing
- poetry build
- tar xvzf dist/minio-service-0.1.0.tar.gz
- poetry run add-logging
- poetry run get-setup
- python setup.py install

Examples

download file from minio

    from minio_service.minio_api import MinioCommunicator
    client = MinioCommunicator()
    client.download_file('bucket', 'minio_path/test.pdf', Path('local_path/test.pdf'))

download directory from minio

    from minio_service.minio_api import MinioCommunicator
    client = MinioCommunicator()
    client.download_directory('bucket', 'minio_path', 'local_dir')

upload file to minio

    from minio_service.minio_api import MinioCommunicator
    client = MinioCommunicator()
    client.upload_file('bucket', 'minio_path/test.pdf', 'test.pdf')

upload directory to minio

    from minio_service.minio_api import MinioCommunicator
    client = MinioCommunicator()
    client.upload_directory('bucket', 'minio_path', 'local_dir')
