import {
    AuthResult,
    AuthResultRaw,
    Credentials,
    MutationHookType,
    User,
    AuthProviderRaw
} from 'api/typings';
import { useMutation, useQuery } from 'react-query';
import { useBadgerFetch } from './api';
import { authCallback } from '../../shared/helpers/auth-tools';

const client_id = process.env.REACT_APP_AUTH_CLIENT_ID as string;
const namespace = process.env.REACT_APP_USERS_API_NAMESPACE;

const auth = useBadgerFetch<AuthResultRaw>({
    url: `${namespace}/token`,
    method: 'post',
    headers: {
        accept: 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    withCredentials: false
});

const authWithEpam = useBadgerFetch<AuthProviderRaw>({
    url: `${namespace}/identity_providers_data`
});

export const useAuthBySSOMutation: MutationHookType<AuthResultRaw, AuthResult> = () =>
    useMutation(async (hashInfo) => Promise.resolve(authCallback(hashInfo)));

export const authWithSSO = () => {
    authWithEpam().then((result) => {
        const url = result['Identity Providers Info'][0]['Auth link'];
        window.location.replace(url);
    });
};

export const useAuthByCredsMutation: MutationHookType<Credentials, AuthResult> = () =>
    useMutation(async (creds) =>
        auth(new URLSearchParams({ grant_type: 'password', ...creds, client_id }).toString()).then(
            (result) => {
                return authCallback(result);
            }
        )
    );

const currentUser = useBadgerFetch<User>({
    url: `${namespace}/users/current_v2`,
    method: 'get'
});

export const useCurrentUser = (isEnabled = true) =>
    useQuery(['currentUser', isEnabled], async () => currentUser(), {
        enabled: isEnabled,
        refetchOnWindowFocus: false,
        cacheTime: 0
    });
