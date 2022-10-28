TEST_IMAGE="test_image"
TEST_TAG="test_tag"
SONAR_TEST_IMAGE="sonar_test_image"
SONAR_TEST_TAG="sonar_test_tag"

build:
	docker build --target build -t ${image_name} .
test:
	echo No test provided
#	docker build --target test -t ${TEST_IMAGE}:${TEST_TAG} .

sonar_test:
	echo No sonar key provided
#	docker build --target sonar \
	-t ${SONAR_TEST_IMAGE}:${SONAR_TEST_TAG} .
	
#	docker run -e SONAR_PROJECT_KEY_PIPELINES=${SONAR_PROJECT_KEY_PIPELINES} \
	-e SONAR_HOST_URL=${SONAR_HOST_URL} -e SONAR_TOKEN_PIPELINES=${SONAR_TOKEN_PIPELINES} \
	-d ${SONAR_TEST_IMAGE}:${SONAR_TEST_TAG}
