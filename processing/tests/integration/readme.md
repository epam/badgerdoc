# How to run tests without integration tests

`pytest -m "not integration"`

# How to run all tests

1. Keep free the ports for services (see `./test-docker-compose.yml`)
2. `pull` last master (integration tests depends on other services)
3. run `pytest . --docker-compose=tests/integration/test-docker-compose.yml` from the service root directory.
