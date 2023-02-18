SHARED_PATH=$(realpath "./conf/shared.env")
ASSETS_PATH="./conf/assets.env"


for service in "assets" "annotation" "jobs" "models" "pipelines" "processing" "scheduler" "taxonomy"
do
  echo "Migrate database for :"$service
  cd "../"$service
  source $SHARED_PATH && alembic upgrade head
done

