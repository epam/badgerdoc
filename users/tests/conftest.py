from unittest.mock import patch

import pytest


@pytest.fixture
def mocked_token1():
    mocked_token1 = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJIY0dZYXVPeV9rN0tQLUpDdlJNUjd5b3BnV2pEc2lob2k0NW8zZElNQ0o0In0.eyJleHAiOjE2NDMwMzA4NDksImlhdCI6MTY0MzAyMzY0OSwiYXV0aF90aW1lIjoxNjQzMDIzNjQ5LCJqdGkiOiJmY2QwOGVhMi00YTVkLTRiYmYtYmIxZS0wOTFjNDM1NGUwZDgiLCJpc3MiOiJodHRwOi8vZGV2Mi5nY292LnJ1L2F1dGgvcmVhbG1zL21hc3RlciIsInN1YiI6Ijc2MDVmNTE4LTg1Y2EtNGQwOS05NmQwLTUzNWZhNGI0MmU1OCIsInR5cCI6IkJlYXJlciIsImF6cCI6IkJhZGdlckRvYyIsInNlc3Npb25fc3RhdGUiOiJjODQ3YTI5Ny04YzdjLTQyMDUtOTQxZi1hZmNiNWViOWNkYjEiLCJhY3IiOiIxIiwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbImNyZWF0ZS1yZWFsbSIsImRlZmF1bHQtcm9sZXMtbWFzdGVyIiwicm9sZS1hbm5vdGF0b3IiLCJvZmZsaW5lX2FjY2VzcyIsImFkbWluIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJtYXN0ZXItcmVhbG0iOnsicm9sZXMiOlsidmlldy1yZWFsbSIsInZpZXctaWRlbnRpdHktcHJvdmlkZXJzIiwibWFuYWdlLWlkZW50aXR5LXByb3ZpZGVycyIsImltcGVyc29uYXRpb24iLCJjcmVhdGUtY2xpZW50IiwibWFuYWdlLXVzZXJzIiwicXVlcnktcmVhbG1zIiwidmlldy1hdXRob3JpemF0aW9uIiwicXVlcnktY2xpZW50cyIsInF1ZXJ5LXVzZXJzIiwibWFuYWdlLWV2ZW50cyIsIm1hbmFnZS1yZWFsbSIsInZpZXctZXZlbnRzIiwidmlldy11c2VycyIsInZpZXctY2xpZW50cyIsIm1hbmFnZS1hdXRob3JpemF0aW9uIiwibWFuYWdlLWNsaWVudHMiLCJxdWVyeS1ncm91cHMiXX0sImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoicHJvZmlsZSBlbWFpbCIsInNpZCI6ImM4NDdhMjk3LThjN2MtNDIwNS05NDFmLWFmY2I1ZWI5Y2RiMSIsInRlbmFudHMiOlsidGVzdCJdLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsIm5hbWUiOiJGZWRvciBTcGlyaWRvbm92IiwicHJlZmVycmVkX3VzZXJuYW1lIjoiZmVkb3Jfc3Bpcmlkb25vdkBlcGFtLmNvbSIsImdpdmVuX25hbWUiOiJGZWRvciIsImZhbWlseV9uYW1lIjoiU3Bpcmlkb25vdiIsImVtYWlsIjoiZmVkb3Jfc3Bpcmlkb25vdkBlcGFtLmNvbSJ9.BPB32jHWl52gBBNkYFtWGhsj9bIeRJN7HmAK-FsWi8nRudrqK-AR9b8ctuZy-hIUIoduCxFmkEwklwerHDBDWuiInScY1r6ntoZfpBY98RQsaJhrTPvIbjXV3o2DkyB-ad1sYXmaKb_xAmR3ur3uAL28baU1MfcwZGwLRUo0Imx2s9ZSIToTOMj7KqVR_nAejZY7W3uZVNVuMlfGf6HQCQG9BHwlz8IidrUp8pL7AsacHi0lRqgrcZzXUjMaKOkNPe_v7f-cGzvcn3-5CqDg59i0qllJHGLv0wZ5Dd0-RUYY_6vM2fombfwPZJcIcg7EWrLM9GMX0qUr11W-i3Bk5A"
    return mocked_token1


@pytest.fixture
def mocked_token1_data():
    mocked_token1_data = {
        "exp": 1643030849,
        "iat": 1643023649,
        "auth_time": 1643023649,
        "jti": "fcd08ea2-4a5d-4bbf-bb1e-091c4354e0d8",
        "iss": "http://dev2.gcov.ru/auth/realms/master",
        "sub": "7605f518-85ca-4d09-96d0-535fa4b42e58",
        "typ": "Bearer",
        "azp": "BadgerDoc",
        "session_state": "c847a297-8c7c-4205-941f-afcb5eb9cdb1",
        "name": "Fedor Spiridonov",
        "given_name": "Fedor",
        "family_name": "Spiridonov",
        "preferred_username": "fedor_spiridonov@epam.com",
        "email": "fedor_spiridonov@epam.com",
        "email_verified": False,
        "acr": "1",
        "realm_access": {
            "roles": [
                "create-realm",
                "default-roles-master",
                "role-annotator",
                "offline_access",
                "admin",
                "uma_authorization",
            ]
        },
        "resource_access": {
            "master-realm": {
                "roles": [
                    "view-realm",
                    "view-identity-providers",
                    "manage-identity-providers",
                    "impersonation",
                    "create-client",
                    "manage-users",
                    "query-realms",
                    "view-authorization",
                    "query-clients",
                    "query-users",
                    "manage-events",
                    "manage-realm",
                    "view-events",
                    "view-users",
                    "view-clients",
                    "manage-authorization",
                    "manage-clients",
                    "query-groups",
                ]
            },
            "account": {
                "roles": [
                    "manage-account",
                    "manage-account-links",
                    "view-profile",
                ]
            },
        },
        "scope": "profile email",
        "sid": "c847a297-8c7c-4205-941f-afcb5eb9cdb1",
        "tenants": ["test"],
        "client_id": "BadgerDoc",
        "username": "fedor_spiridonov@epam.com",
        "active": True,
    }


@pytest.fixture
def mocked_admin_auth_data():
    mocked_admin_auth_data = {
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJIY0dZYXVPeV9rN0tQLUpDdlJNUjd5b3BnV2pEc2lob2k0NW8zZElNQ0o0In0.eyJleHAiOjE2NDMzODM5NzEsImlhdCI6MTY0MzAyMzk3MSwianRpIjoiZTYwODg5YWItOTcyOC00ODUxLThjOTMtMjQ5ZGRlY2Y2YmRiIiwiaXNzIjoiaHR0cDovL2RldjIuZ2Nvdi5ydS9hdXRoL3JlYWxtcy9tYXN0ZXIiLCJzdWIiOiIwMjMzNjY0Ni1mNWQwLTQ2NzAtYjExMS1jMTQwYTNhZDU4YjUiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhZG1pbi1jbGkiLCJzZXNzaW9uX3N0YXRlIjoiYWM0NGJkMjYtNDQzMy00YmRkLTk0YmQtOGJlMTQ0NTQxYTE4IiwiYWNyIjoiMSIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJjcmVhdGUtcmVhbG0iLCJyb2xlLWFubm90YXRvciIsImFkbWluIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsibWFzdGVyLXJlYWxtIjp7InJvbGVzIjpbInZpZXctcmVhbG0iLCJ2aWV3LWlkZW50aXR5LXByb3ZpZGVycyIsIm1hbmFnZS1pZGVudGl0eS1wcm92aWRlcnMiLCJpbXBlcnNvbmF0aW9uIiwiY3JlYXRlLWNsaWVudCIsIm1hbmFnZS11c2VycyIsInF1ZXJ5LXJlYWxtcyIsInZpZXctYXV0aG9yaXphdGlvbiIsInF1ZXJ5LWNsaWVudHMiLCJxdWVyeS11c2VycyIsIm1hbmFnZS1ldmVudHMiLCJtYW5hZ2UtcmVhbG0iLCJ2aWV3LWV2ZW50cyIsInZpZXctdXNlcnMiLCJ2aWV3LWNsaWVudHMiLCJtYW5hZ2UtYXV0aG9yaXphdGlvbiIsIm1hbmFnZS1jbGllbnRzIiwicXVlcnktZ3JvdXBzIl19fSwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwic2lkIjoiYWM0NGJkMjYtNDQzMy00YmRkLTk0YmQtOGJlMTQ0NTQxYTE4IiwidGVuYW50cyI6WyJ0ZXN0Il0sImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwicHJlZmVycmVkX3VzZXJuYW1lIjoiYWRtaW4ifQ.dOsbOt9XjZUhXx0B85scJVa55jUaWym7M4S2piLGmZykhTe6bavPpbDPvJ1LUZIQ22TtWEAemkK1JVglEEy8F6JH5U-glvea9bd-JA-ZyS5eFI4PROQdWR1N7POLphXtdwXzgqaR2MaHx5nQ76I3ynwQnIuqZUTfFQZehgYpCc4pp1eF90sgBlzgqRe67HS_5jD1apBCKbTPHaevHQqa1H32Hqj2iUrXUE-44v1QDKnp756xEMMZPSmsB_IfnZePrCsRwM1PuQg6FRvBn_eOLeI91SFsnLuvf_0FmxA4QK-Rhdek_MPjDSYY_R0G81tEMVGzjo6ZkHYilt-_7aFViQ",
        "expires_in": 360000,
        "refresh_expires_in": 1800,
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICIzOTZkZTVhOC0xNzU1LTQ2ODQtYjVlNS1kODU0OTRkN2JmYzIifQ.eyJleHAiOjE2NDMwMjU3NzEsImlhdCI6MTY0MzAyMzk3MSwianRpIjoiZjA5Mjc2MTQtYTBmNi00YmJlLWFhMGQtNjFhMTQ0ZjRlNjQ3IiwiaXNzIjoiaHR0cDovL2RldjIuZ2Nvdi5ydS9hdXRoL3JlYWxtcy9tYXN0ZXIiLCJhdWQiOiJodHRwOi8vZGV2Mi5nY292LnJ1L2F1dGgvcmVhbG1zL21hc3RlciIsInN1YiI6IjAyMzM2NjQ2LWY1ZDAtNDY3MC1iMTExLWMxNDBhM2FkNThiNSIsInR5cCI6IlJlZnJlc2giLCJhenAiOiJhZG1pbi1jbGkiLCJzZXNzaW9uX3N0YXRlIjoiYWM0NGJkMjYtNDQzMy00YmRkLTk0YmQtOGJlMTQ0NTQxYTE4Iiwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwic2lkIjoiYWM0NGJkMjYtNDQzMy00YmRkLTk0YmQtOGJlMTQ0NTQxYTE4In0.NO_5jSn7F3mre0kBW8rDXPcRHNZhs6bUfwSb0wBackk",
        "token_type": "Bearer",
        "id_token": None,
        "not-before-policy": 0,
        "session_state": "ac44bd26-4433-4bdd-94bd-8be144541a18",
        "scope": "profile email",
    }
    return mocked_admin_auth_data


@pytest.fixture
def mocked_identity_providers_data():
    mocked_identity_providers_data = [
        {
            "alias": "EPAM_SSO",
            "displayName": "EPAM SSO",
            "internalId": "9b061b13-9d77-4dd3-a4dd-7bf834ac58cd",
            "providerId": "saml",
            "enabled": True,
            "updateProfileFirstLoginMode": "on",
            "trustEmail": False,
            "storeToken": False,
            "addReadTokenRoleOnCreate": False,
            "authenticateByDefault": False,
            "linkOnly": False,
            "firstBrokerLoginFlowAlias": "first broker login",
            "config": {
                "validateSignature": "true",
                "signingCertificate": "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",
                "postBindingLogout": "true",
                "postBindingResponse": "true",
                "nameIDPolicyFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                "entityId": "http://dev2.gcov.ru/auth/realms/master",
                "xmlSigKeyInfoKeyNameTransformer": "KEY_ID",
                "signatureAlgorithm": "RSA_SHA256",
                "useJwksUrl": "true",
                "loginHint": "false",
                "allowCreate": "true",
                "syncMode": "FORCE",
                "authnContextComparisonType": "exact",
                "postBindingAuthnRequest": "true",
                "wantAuthnRequestsSigned": "true",
                "singleSignOnServiceUrl": "https://access-staging.epam.com/auth/realms/plusx/protocol/saml",
                "addExtensionsElementWithKeyInfo": "false",
                "principalType": "SUBJECT",
            },
        }
    ]
    return mocked_identity_providers_data
