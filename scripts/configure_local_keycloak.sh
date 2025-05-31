#!/bin/bash

KEYCLOAK_USER="${KEYCLOAK_USER:=admin}"
KEYCLOAK_PASSWORD="${KEYCLOAK_PASSWORD:=admin}"

ACCESS_TOKEN=$(curl -X POST http://localhost:8082/auth/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${KEYCLOAK_USER}" \
  -d "password=${KEYCLOAK_PASSWORD}" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

# Go to Realm Settings -> Keys and disable RSA-OAEP algorithm. It will help to avoid issue explainded here https://github.com/jpadilla/pyjwt/issues/722
RSA_OAEP_COMPONENT_ID=$(curl -X GET http://localhost:8082/auth/admin/realms/master/components?type=org.keycloak.keys.KeyProvider \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq -r '.[] | select(.config.algorithm[]? == "RSA-OAEP") | .id')

curl -X PUT http://localhost:8082/auth/admin/realms/master/components/${RSA_OAEP_COMPONENT_ID} \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "${RSA_OAEP_COMPONENT_ID}",
    "name": "rsa-enc-generated",
    "providerId": "rsa-enc-generated",
    "providerType": "org.keycloak.keys.KeyProvider",
    "config": {
      "priority": ["100"],
      "enabled": ["false"],
      "active": ["false"],
      "algorithm": ["RSA-OAEP"],
      "keySize": ["2048"]
    }
  }'

if [ $? -ne 0 ]; then
  echo "Failed to disable RSA-OAEP key provider."
  exit 1
else
  echo "RSA-OAEP key provider disabled successfully."
fi

# # Add tenant attribute to admin user, go to Users -> select admin -> go to Attributes -> create attribute tenants:local, and save
KEYCLOAK_USER_ID=$(curl -X GET http://localhost:8082/auth/admin/realms/master/users?username=${KEYCLOAK_USER} \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq -r '.[0].id')
curl -X PUT http://localhost:8082/auth/admin/realms/master/users/${KEYCLOAK_USER_ID}/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "attributes": {
      "tenants": ["local"]
    }
  }'
if [ $? -ne 0 ]; then
  echo "Failed to add tenant attribute to admin user."
  exit 1
else
  echo "Tenant attribute added to admin user successfully."
fi

# # Go to Clients -> admin-cli -> Mappers -> Create and fill form with following values:
# # Param	Value
# # Protocol	openid-connect
# # Name	tenants
# # Mapper Type	User Attribute
# # User Attribute	tenants
# # Token Claim Name	tenants
# # Claim JSON Type	string
# # Add to ID token	On
# # Add to access token	On
# # Add to userinfo	On
# # Multivalued	On
# # Aggregate attribute values	On
CLIENT_ID=$(curl -X GET http://localhost:8082/auth/admin/realms/master/clients?clientId=admin-cli \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq -r '.[0].id')
curl -X POST http://localhost:8082/auth/admin/realms/master/clients/${CLIENT_ID}/protocol-mappers/models \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "tenants",
    "protocol": "openid-connect",
    "protocolMapper": "oidc-usermodel-attribute-mapper",
    "consentRequired": false,
    "config": {
      "user.attribute": "tenants",
      "claim.name": "tenants",
      "jsonType.label": "String",
      "access.token.claim": true,
      "id.token.claim": true,
      "userinfo.token.claim": true,
      "multivalued": true,
      "aggregate.attrs": true
    }
  }'
if [ $? -ne 0 ]; then
  echo "Failed to create tenants mapper."
  exit 1
else
  echo "Tenants mapper created successfully."
fi

# # Go to Client Scopes -> Find roles -> Scope and select admin in list to add to Assigned Roles, then go to Mappers and ensure that only 2 mappers exists: realm roles and client roles. Delete all other mappers
CLIENT_SCOPE_ID=$(curl -X GET http://localhost:8082/auth/admin/realms/master/client-scopes \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq -r '.[] | select(.name == "roles") | .id')
ADMIN_ROLE_ID=$(curl -X GET "http://localhost:8082/auth/admin/realms/master/roles" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" | jq -r '.[] | select(.name == "admin") | .id')
curl -X POST "http://localhost:8082/auth/admin/realms/master/client-scopes/$CLIENT_SCOPE_ID/scope-mappings/realm" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": "'$ADMIN_ROLE_ID'",
      "name": "admin"
    }
  ]'

curl -s -X GET "http://localhost:8082/auth/admin/realms/master/client-scopes/$CLIENT_SCOPE_ID/protocol-mappers/models" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | \
  jq -r '.[] | select(.name != "realm roles" and .name != "client roles") | .id' | \
  while read MAPPER_ID; do
    echo "Deleting mapper: $MAPPER_ID"
    curl -X DELETE "http://localhost:8082/auth/admin/realms/master/client-scopes/$CLIENT_SCOPE_ID/protocol-mappers/models/$MAPPER_ID" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}"
  done
if [ $? -ne 0 ]; then
  echo "Failed to create admin mapper in Find roles client scope."
  exit 1
else
  echo "Admin mapper created successfully in Find roles client scope."
fi

# # Go to Clients -> Create -> Fill form and save

# # Param	Value
# # Client ID	badgerdoc-internal
# # Client Protocol	openid-connect
curl -X POST http://localhost:8082/auth/admin/realms/master/clients \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "badgerdoc-internal",
    "protocol": "openid-connect",
    "enabled": true,
    "publicClient": false,
    "serviceAccountsEnabled": true,
    "authorizationServicesEnabled": true,
    "redirectUris": ["_"],
    "webOrigins": ["_"]
  }'
if [ $? -ne 0 ]; then
  echo "Failed to create badgerdoc-internal client."
  exit 1
else
  echo "Badgerdoc-internal client created successfully."
fi

# Now you can Credentials tab, open it and copy Secret
# Then Client ID and Secret must be set to .env as KEYCLOAK_SYSTEM_USER_CLIENT=badgerdoc-internal and KEYCLOAK_SYSTEM_USER_SECRET to copied key
CLIENT_UUID=$(curl -X GET http://localhost:8082/auth/admin/realms/master/clients \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" | jq -r '.[] | select(.clientId == "badgerdoc-internal") | .id')

CLIENT_SECRET=$(curl -X GET http://localhost:8082/auth/admin/realms/master/clients/${CLIENT_UUID}/client-secret \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" | jq -r '.value')

echo Change value of KEYCLOAK_SYSTEM_USER_SECRET in .env to $CLIENT_SECRET

# Go to Clients -> Find badgerdoc-internal -> Service Account Roles -> Client Roles -> master-realm -> Find view-users and view-identity-providers in Available Roles and add to Assigned Roles

SERVICE_ACCOUNT_USER_ID=$(curl -X GET "http://localhost:8082/auth/admin/realms/master/clients/$CLIENT_UUID/service-account-user" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" | jq -r '.id')

MASTER_REALM_CLIENT_ID=$(curl -X GET "http://localhost:8082/auth/admin/realms/master/clients" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" | jq -r '.[] | select(.clientId == "master-realm") | .id')

ROLES_JSON=$(curl -s -X GET "http://localhost:8082/auth/admin/realms/master/clients/$MASTER_REALM_CLIENT_ID/roles" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | \
  jq '[.[] | select(.name == "view-users" or .name == "view-identity-providers")]')

echo "Roles to assign: $ROLES_JSON"

curl -X POST "http://localhost:8082/auth/admin/realms/master/users/$SERVICE_ACCOUNT_USER_ID/role-mappings/clients/$MASTER_REALM_CLIENT_ID" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$ROLES_JSON"

if [ $? -ne 0 ]; then
  echo "Failed to assign roles to badgerdoc-internal service account."
  exit 1
else
  echo "Roles assigned to badgerdoc-internal service account successfully."
fi

# Go to Roles -> add roles: presenter, manager, role-annotator, annotator, engineer. Open admin role, go to Composite Roles -> Realm Roles and add all these roles

ROLES=("presenter" "manager" "role-annotator" "annotator" "engineer")

for role in "${ROLES[@]}"; do
    echo "Creating role: $role"
    curl -X POST "http://localhost:8082/auth/admin/realms/master/roles" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{\"name\": \"$role\", \"description\": \"$role role\"}"
    echo ""
done

ROLES_JSON=$(curl -s -X GET "http://localhost:8082/auth/admin/realms/master/roles" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | \
  jq '[.[] | select(.name == "presenter" or .name == "manager" or .name == "role-annotator" or .name == "annotator" or .name == "engineer") | {id: .id, name: .name}]')

echo "Roles JSON: $ROLES_JSON"

curl -X POST "http://localhost:8082/auth/admin/realms/master/roles/admin/composites" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$ROLES_JSON"

if [ $? -ne 0 ]; then
  echo "Failed to assign roles to badgerdoc-internal service account."
  exit 1
else
  echo "Roles assigned to badgerdoc-internal service account successfully."
fi

# Go to Realm Settings -> Tokens -> Find Access Token Lifespan and set 1 Days
curl -X PUT "http://localhost:8082/auth/admin/realms/master" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "accessTokenLifespan": 86400
  }'