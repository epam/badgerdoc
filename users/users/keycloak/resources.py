"""Keycloak resource endpoints."""

from functools import reduce
from string import Template
from urllib.parse import urljoin

from users.config import KEYCLOAK_HOST


def join_paths(*args: str) -> str:
    """Join paths."""
    return reduce(urljoin, map(lambda x: x.strip("/") + "/", args))


_base_uri = join_paths(KEYCLOAK_HOST, "auth")
_base_uri_admin = join_paths(_base_uri, "admin")

_realm_uri = join_paths("realms", "$realm")
_protocol_uri = join_paths("protocol", "$protocol")
_roles_uri = join_paths("roles", "$role")
_oidc_uri = join_paths(
    _realm_uri, Template(_protocol_uri).substitute(protocol="openid-connect")
)

auth_uri = Template(join_paths(_base_uri, _oidc_uri, "auth"))
token_uri = Template(join_paths(_base_uri, _oidc_uri, "token"))
users_uri = Template(join_paths(_base_uri_admin, _realm_uri, "users"))
user_uri = Template(join_paths(users_uri.template, "$id"))
groups_uri = Template(join_paths(_base_uri_admin, _realm_uri, "groups"))
users_by_role_uri = Template(
    join_paths(_base_uri_admin, _realm_uri, _roles_uri, "users")
)
execute_actions_email_uri = Template(
    join_paths(user_uri.template, "execute-actions-email")
)

token_introspection_uri = Template(
    join_paths(_base_uri, _oidc_uri, "token", "introspect")
)
identity_providers_uri = Template(
    join_paths(
        _base_uri, "admin", _realm_uri, "identity-provider", "instances"
    )
)
