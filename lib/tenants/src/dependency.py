from typing import Optional, Union

import jwt
from fastapi import HTTPException, Request, status
from fastapi.openapi.models import HTTPBearer
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param

from .schema import TenantData


class TenantDependencyBase:
    def __init__(self, key: str, algorithm: str = "HS256") -> None:
        self.key = key
        self.algorithm = algorithm

    async def __call__(self, request: Request) -> TenantData:
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authorization provided!",
            )

        _, token = get_authorization_scheme_param(authorization)
        try:
            decoded = jwt.decode(token, self.key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is expired!",
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is invalid!",
            )

        tenant = decoded.get("tenant")
        roles = decoded.get("roles")
        user_id = decoded.get("user_id")
        if not (tenant and roles and user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wrong data provided in jwt!",
            )

        return TenantData(user_id=user_id, roles=roles, tenant=tenant)


class TenantDependencyDocs(TenantDependencyBase, SecurityBase):  # type: ignore
    def __init__(
        self,
        key: str,
        algorithm: str = "HS256",
        scheme_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        super().__init__(key, algorithm)
        self.model = HTTPBearer(description=description)
        self.scheme_name = scheme_name or self.__class__.__name__


def get_tenant_info(
    key: str,
    algorithm: str = "HS256",
    scheme_name: Optional[str] = None,
    description: Optional[str] = None,
    debug: bool = False,
) -> Union[TenantDependencyBase, TenantDependencyDocs]:
    if debug:
        return TenantDependencyDocs(key, algorithm, scheme_name, description)
    return TenantDependencyBase(key, algorithm)
