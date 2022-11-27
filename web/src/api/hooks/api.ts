import { ApiError } from 'api/api-error';
import { applyMocks } from 'api/mocks';
import { getAuthHeaders, refetchToken } from 'shared/helpers/auth-tools';

type BadgerFetchOptions = {
    url: string;
    method?: 'post' | 'get' | 'delete' | 'put';
    headers?: string[][] | Record<string, string> | Headers;
    withCredentials?: boolean;
    plainHeaders?: boolean;
    isBlob?: boolean;
};
export type BadgerFetchBody =
    | ReadableStream
    | Blob
    | ArrayBufferView
    | ArrayBuffer
    | FormData
    | URLSearchParams
    | string
    | null;
export type BadgerFetch<ResponseDataT> = (body?: BadgerFetchBody) => Promise<ResponseDataT>;

export type BadgerFetchProvider = <ResponseDataT>(
    arg: BadgerFetchOptions
) => BadgerFetch<ResponseDataT>;

let useBadgerFetch: BadgerFetchProvider = (arg) => {
    return async (body) => {
        const {
            url,
            method = 'get',
            headers,
            withCredentials = true,
            plainHeaders = false,
            isBlob = false
        } = arg;
        const combinedHeaders = {};

        if (withCredentials) {
            Object.assign(combinedHeaders, {
                ...getAuthHeaders()
            });
        }

        if (!plainHeaders) {
            Object.assign(combinedHeaders, {
                'Content-Type': 'application/json'
            });
        }

        const response = await fetch(url, {
            method,
            body,
            headers: {
                ...combinedHeaders,
                ...headers
            }
        });
        const { status, statusText } = response;
        if (status >= 500) {
            throw new ApiError(statusText, 'Please contact DevOps Support Team', {
                status,
                detail: null
            });
        } else {
            let responseBody;
            if (isBlob) {
                responseBody = await response.blob();
            } else responseBody = await response.json();
            if (!response.ok) {
                if (status === 403) {
                    const refetchSuccess = await refetchToken();
                    if (refetchSuccess) {
                        useBadgerFetch(arg);
                    }
                }
                if (status === 401) {
                    location.href = '/login';
                }
                // by default in summary details, but you can overload it with useful message inside your api hooks
                const summary =
                    status === 401
                        ? 'Wrong credentials, you will be redirected to login page...'
                        : responseBody.detail;
                throw new ApiError(response.statusText, summary, {
                    status,
                    ...responseBody
                });
            }

            return responseBody;
        }
    };
};

const isMocksAllowed = String(process.env.REACT_APP_ALLOW_MOCKS).toLocaleLowerCase() == 'true';

if (isMocksAllowed) {
    useBadgerFetch = applyMocks(useBadgerFetch);
}

export { useBadgerFetch };
