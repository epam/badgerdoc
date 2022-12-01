import os
import urllib.parse

from fastapi import Header

HEADER_TENANT = "X-Current-Tenant"

X_CURRENT_TENANT_HEADER = Header(..., alias=HEADER_TENANT, example="test")
