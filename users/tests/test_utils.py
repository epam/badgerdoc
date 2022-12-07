from unittest.mock import patch

import pytest
from src import utils


def test_extract_idp_data_needed():
    mocked_data_to_convert = [
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
                "signingCertificate": "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",  # noqa: E501
                "postBindingLogout": "true",
                "postBindingResponse": "true",
                "nameIDPolicyFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",  # noqa: E501
                "entityId": "http://dev2.badgerdoc.com/auth/realms/master",
                "xmlSigKeyInfoKeyNameTransformer": "KEY_ID",
                "signatureAlgorithm": "RSA_SHA256",
                "useJwksUrl": "true",
                "loginHint": "false",
                "allowCreate": "true",
                "syncMode": "FORCE",
                "authnContextComparisonType": "exact",
                "postBindingAuthnRequest": "true",
                "wantAuthnRequestsSigned": "true",
                "singleSignOnServiceUrl": "https://access-staging.epam.com/auth/realms/plusx/protocol/saml",  # noqa: E501
                "addExtensionsElementWithKeyInfo": "false",
                "principalType": "SUBJECT",
            },
        }
    ]
    assert utils.extract_idp_data_needed(mocked_data_to_convert) == [
        {
            "Alias": "EPAM_SSO",
            "Auth link": "http://dev2.badgerdoc.com/auth/realms/master/protocol/openid-connect/auth?client_id=BadgerDoc&response_type=token&redirect_uri=http://dev2.badgerdoc.com/login&kc_idp_hint=EPAM_SSO",  # noqa: E501
        }
    ]


@pytest.mark.parametrize(
    ("prefix", "expected"), (("", "tenant"), ("prefix", "prefix-tenant"))
)
def test_bucket_dependency(prefix: str, expected: str) -> None:
    with patch("src.config.S3_PREFIX", prefix):
        assert utils.get_bucket_name("tenant") == expected
