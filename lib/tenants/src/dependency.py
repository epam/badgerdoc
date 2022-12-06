from typing import Any, Dict, Optional, Union

import jwt
from fastapi import HTTPException, Request, status
from fastapi.openapi.models import HTTPBearer
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param

from .schema import SupportedAlgorithms, TenantData


class TenantDependencyBase:
    def __init__(
        self,
        key: str = "",
        algorithm: str = "RS256",
        url: str = "http://bagerdoc-keycloack",
    ) -> None:
        """
        For usage with alg HS256 you must provide 'key' and 'alg' arguments.
        For usage with alg RS256 you must provide 'url' and 'alg' arguments.

        Args:
            key: a private key for decoding tokens with hs256 alg
            algorithm: an alg for tokens, will be checked in available algorithms  # noqa
            url: an url to auth service (http://bagerdoc-keycloack, http://dev1.gcov.ru)  # noqa
        """
        self.key = key
        self.algorithm = self._check_algorithm(algorithm)
        self.jwk_client: jwt.PyJWKClient = jwt.PyJWKClient(
            self._create_url(url)
        )

    async def __call__(self, request: Request) -> TenantData:
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authorization provided!",
            )
        current_tenant: str = request.headers.get("X-Current-Tenant")
        if not current_tenant:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No X-Current-Tenant provided!",
            )
        _, token = get_authorization_scheme_param(authorization)
        decoded: Dict[str, Any] = {}
        if self.algorithm == SupportedAlgorithms.HS256:
            decoded = self.decode_hs256(token)
        elif self.algorithm == SupportedAlgorithms.RS256:
            decoded = self.decode_rs256(token)

        sub = decoded.get("sub")
        realm_access = decoded.get("realm_access")
        roles = False
        if realm_access:
            roles = realm_access.get("roles")
        tenants = decoded.get("tenants")

        if decoded.get("clientId") == "pipelines":
            return TenantData(
                token=token, user_id=sub, roles=roles, tenants=tenants
            )

        if not (sub and roles and tenants):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wrong data provided in jwt!",
            )

        if current_tenant not in tenants:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="X-Current-Tenant not in jwt tenants!",
            )

        return TenantData(
            token=token, user_id=sub, roles=roles, tenants=tenants
        )

    def decode_hs256(self, token: str) -> Dict[str, Any]:
        try:
            decoded = jwt.decode(token, self.key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is expired!",
            )
        except (jwt.PyJWTError, jwt.exceptions.DecodeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is invalid!",
            )
        return decoded

    def decode_rs256(self, token: str) -> Dict[str, Any]:
        try:
            signing_key = self.jwk_client.get_signing_key_from_jwt(token)
            decoded = jwt.decode(
                token, signing_key.key, algorithms=[self.algorithm]
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is expired!",
            )
        except (jwt.PyJWTError, jwt.exceptions.DecodeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is invalid!",
            )
        return decoded

    @staticmethod
    def _check_algorithm(alg: str) -> str:
        if alg not in SupportedAlgorithms.members():
            raise ValueError(
                f"Available algorithms {SupportedAlgorithms.members()}"
            )
        return alg

    @staticmethod
    def _create_url(url: str) -> str:
        auth_path = "auth/realms/master/protocol/openid-connect/certs"
        return url.rstrip("/") + "/" + auth_path


class TenantDependencyDocs(TenantDependencyBase, SecurityBase):
    def __init__(
        self,
        key: str = "",
        algorithm: str = "RS256",
        url: str = "http://bagerdoc-keycloack",
        scheme_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        super().__init__(key, algorithm, url)
        self.model = HTTPBearer(description=description)
        self.scheme_name = scheme_name or self.__class__.__name__


def get_tenant_info(
    key: str = "",
    algorithm: str = "RS256",
    url: str = "http://bagerdoc-keycloack",
    scheme_name: Optional[str] = None,
    description: Optional[str] = None,
    debug: bool = True,
) -> Union[TenantDependencyBase, TenantDependencyDocs]:
    """
    For usage with alg HS256 you must provide 'key' and 'alg' arguments.
    For usage with alg RS256 you must provide 'url' and 'alg' arguments.

    Examples:
        RS256:
            tenant = get_tenant_info(algorithm="RS256", url="http://dev1.gcov.ru").  # noqa
        HS256:
            tenant = get_tenant_info(algorithm="HS256", key="some_secret_key").  # noqa

    Args:
        key: a private key for decoding tokens with hs256 alg.
        algorithm: an alg for tokens, will be checked in available algorithms.
        url: an url to auth service (http://bagerdoc-keycloack, http://dev1.gcov.ru).  # noqa
        scheme_name: a name for TenantDependency on Swagger, if not provided class name will be used.  # noqa
        description: a description for TenantDependency on Swagger, if not provided description will be empty.  # noqa
        debug: If True button 'Authorize' will be rendered on Swagger.
    """
    if debug:
        return TenantDependencyDocs(
            key, algorithm, url, scheme_name, description
        )
    return TenantDependencyBase(key, algorithm, url)
