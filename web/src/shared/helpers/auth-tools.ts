// temporary_disabled_rules
/* eslint-disable react-hooks/rules-of-hooks */
import { AuthResult, AuthResultRaw, StoredAuthResult } from 'api/typings';
import Cookies from 'universal-cookie';
import { useBadgerFetch } from '../../api/hooks/api';

const cookies = new Cookies();
const AUTH_DETAILS_ID = 'auth-details-id';
const AUTH_CURRENT_TENANT = 'auth-current-tenant';
const DEFAULT_REFRESH_INTERVAL = 60000;

const namespace = process.env.REACT_APP_USERS_API_NAMESPACE;

const parseJwt = (token: string) => {
    try {
        return JSON.parse(atob(token.split('.')[1]));
    } catch (e) {
        return null;
    }
};

export const authCallback = (authResult: AuthResultRaw) => {
    const jwt = parseJwt(authResult.access_token);
    const result: AuthResult = jwt
        ? {
              accessToken: authResult.access_token,
              refreshToken: authResult.refresh_token,
              tenants: jwt.tenants || [],
              expiresIn: authResult.expires_in
          }
        : { accessToken: null, refreshToken: null, tenants: [], expiresIn: 0 };
    return result;
};

export const setAuthDetails = (result: AuthResult) => {
    const refreshInterval = (result.expiresIn / 10) * 1000;
    const data: StoredAuthResult = {
        authResult: result,
        updateAtTimestamp: Date.now() + result.expiresIn * 1000 - refreshInterval * 2,
        refreshInterval
    };
    return localStorage.setItem(AUTH_DETAILS_ID, JSON.stringify(data));
};

export const setCurrentTenant = (tenant: string) =>
    localStorage.setItem(AUTH_CURRENT_TENANT, tenant);

const getStoredAuthDetails = (): StoredAuthResult => {
    const authDetails = localStorage.getItem(AUTH_DETAILS_ID)!;
    if (!authDetails) {
        return {
            updateAtTimestamp: 0,
            refreshInterval: DEFAULT_REFRESH_INTERVAL
        };
    }
    return JSON.parse(authDetails);
};

const getAuthDetails = (): AuthResult | null => {
    const data: StoredAuthResult = getStoredAuthDetails();
    return data.authResult || null;
};

export const getCurrentTenant = (): string => localStorage.getItem(AUTH_CURRENT_TENANT)!;

export const refetchToken = async () => {
    const refetch = useBadgerFetch<AuthResultRaw>({
        url: `${namespace}/refresh_token`,
        method: 'post',
        headers: {
            accept: 'application/json'
        },
        withCredentials: false
    });

    const client_id = process.env.REACT_APP_AUTH_CLIENT_ID as string;
    const data: StoredAuthResult = getStoredAuthDetails();
    const refresh_token = data.authResult?.refreshToken || '';

    const result = await refetch(
        JSON.stringify({
            grant_type: 'refresh_token',
            client_id,
            refresh_token
        })
    );

    if (result.access_token) {
        setAuthDetails(authCallback(result));
        return true;
    } else {
        return false;
    }
};

export const getAuthHeaders = () => {
    const details = getAuthDetails();
    const tenant = getCurrentTenant();

    return {
        'X-Current-Tenant': tenant,
        Authorization: 'Bearer ' + details?.accessToken
    };
};

export const clearAuthDetails = () => {
    localStorage.removeItem(AUTH_DETAILS_ID);
    localStorage.removeItem(AUTH_CURRENT_TENANT);
    cookies.set(AUTH_DETAILS_ID, '');
    cookies.set(AUTH_CURRENT_TENANT, '');
};

export const setUpdateTokenInterval = () => {
    const storedAuthDetails = getStoredAuthDetails();
    setInterval(() => {
        const currentTimestamp = Date.now();
        if (!storedAuthDetails || currentTimestamp > storedAuthDetails.updateAtTimestamp) {
            refetchToken();
        }
    }, storedAuthDetails?.refreshInterval || DEFAULT_REFRESH_INTERVAL);
};
