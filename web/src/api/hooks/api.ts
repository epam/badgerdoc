// temporary_disabled_rules
/* eslint-disable react-hooks/rules-of-hooks, no-restricted-globals, eqeqeq */
import { ApiError } from 'api/api-error';
import { applyMocks } from 'api/mocks';
import { HTTPRequestMethod } from 'api/typings';
import { getAuthHeaders, refetchToken } from 'shared/helpers/auth-tools';
import { UploadIndicatorContextType } from 'components/upload-indicator/upload-indicator.context';
import { trackUploadProgress } from './track-upload-progress';

type BadgerFetchOptions = {
    url: string;
    method?: HTTPRequestMethod;
    headers?: string[][] | Record<string, string> | Headers;
    withCredentials?: boolean;
    plainHeaders?: boolean;
    isBlob?: boolean;
    signal?: AbortSignal;
    isFileUpload?: boolean;
    uploadIndicatorContext?: UploadIndicatorContextType;
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
            headers: rawHeaders,
            withCredentials = true,
            plainHeaders = false,
            isBlob = false,
            signal,
            isFileUpload = false,
            uploadIndicatorContext
        } = arg;
        const combinedHeaders = {};

        if (withCredentials) {
            Object.assign(combinedHeaders, {
                ...getAuthHeaders()
            });
        }

        const contentType = isFileUpload ? 'multipart/form-data' : 'application/json';

        if (!plainHeaders) {
            Object.assign(combinedHeaders, {
                'Content-Type': contentType
            });
        }

        const headers = {
            ...combinedHeaders,
            ...rawHeaders
        };

        let response: Response = {} as Response;
        if (isFileUpload) {
            response = await trackUploadProgress(
                url,
                method,
                uploadIndicatorContext,
                body as FormData,
                headers
            );
        } else {
            response = await fetch(url, {
                method,
                body,
                signal,
                headers
            });
        }
        const { status, statusText } = response;
        if (status >= 500) {
            throw new ApiError(statusText, 'Please contact DevOps Support Team', {
                status,
                detail: null
            });
        } else {
            let responseBody;
            if (isBlob) {
                responseBody = response.ok ? await response.blob() : await response.json();
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
