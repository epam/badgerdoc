import { AuthResult, AuthResultRaw, StoredAuthResult } from 'api/typings';
import Cookies from 'universal-cookie';
import { useBadgerFetch } from '../../api/hooks/api';

const cookies = new Cookies();
const AUTH_DETAILS_ID = 'auth-details-id';
const AUTH_CURRENT_TENNANT = 'auth-current-tenant';
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
              jwt: authResult.access_token,
              tenants: jwt.tenants || [],
              expiresIn: authResult.expires_in
          }
        : { jwt: null, tenants: [], expiresIn: 0 };
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
    localStorage.setItem(AUTH_CURRENT_TENNANT, tenant);

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

export const getCurrentTenant = (): string => localStorage.getItem(AUTH_CURRENT_TENNANT)!;

export const refetchToken = async () => {
    const refetch = useBadgerFetch<AuthResultRaw>({
        url: `${namespace}/refresh`,
        method: 'post',
        headers: {
            accept: 'application/json'
        },
        withCredentials: false
    });
    const result = await refetch(new URLSearchParams({ grant_type: 'password' }).toString());
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
        ['X-Current-Tenant']: tenant,
        Authorization: 'Bearer ' + details?.jwt
    };
};

export const clearAuthDetails = () => {
    cookies.set(AUTH_DETAILS_ID, '');
    cookies.set(AUTH_CURRENT_TENNANT, '');
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
