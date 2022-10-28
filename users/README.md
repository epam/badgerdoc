# users filter
Accepts a substring of the user name.\
Extracts all users from keycloak by the specified substring.\
Gives the id and username of all found users

## Setup
`$ docker-compose up`
`$ uvicorn src.main:app`

## Endpoint
`/users/search`

## How to use
#### To get all users by role-annotator and username
create POST query with body:

    {
      "filters": [
        {
          "field": "name",
          "operator": "like",
          "value": <user substring>
        },
        {
          "field": "role",
          "operator": "eq",
          "value": "role-annotator"
        }
      ]
    }

in the `<user substring>` field, enter a substring of the user name

#### To get all users by username
create POST query with body:

    {
      "filters": [
        {
          "field": "name",
          "operator": "like",
          "value": <user substring>
        }
      ]
    }

#### To get all users by role-annotator
create POST query with body:

    {
      "filters": [
        {
          "field": "role",
          "operator": "eq",
          "value": "role-annotator"
        }
      ]
    }

#### To get all users
create POST query with body:

    {}

or:

    {
      "filters": []
    }
