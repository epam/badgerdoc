## Running dataset manager in Docker
### Before you start:
If you have running postgres on your machine, please stop it and make port 5432 (default for postgres) available for
postgres container. To check which app is using 5432 port run:

    sudo lsof -i :5432
To stop postgres:

    sudo service postgresql stop
If you have stopped postgres, but port 5432 still unavailable you can use:

    sudo kill <pid>

As well as postgres, minio should be stopped on your machine. Minio container uses port 9000 so make sure it is available.
### Run docker-compose:

1. Clone this repo
2. Run


    docker-compose up -d


FastAPI docs -> 127.0.0.1:8000/docs

Minio client ->  127.0.0.1:9000 login/password = minioadmin/minioadmin

Make sure to create a bucket by a corresponding endpoint before uploading/deleting files.


Migrations are done so once containers are ready you can use the app:
