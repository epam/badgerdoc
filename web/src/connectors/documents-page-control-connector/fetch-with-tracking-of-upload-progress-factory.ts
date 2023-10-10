import { BadgerCustomFetch } from 'api/hooks/api';
import { UploadProgressTracker } from './use-fetch-with-tracking-of-upload-progress';
import { ApiError } from 'api/api-error';

const calculateProgress = (loaded: number, total: number): number => {
    return Math.floor(100 * (loaded / total));
};

const handleUploadFailed = (xhr: XMLHttpRequest, externalCallback: () => void) => {
    externalCallback();
    throw new ApiError(xhr.statusText, `Upload failed with status ${xhr.status}`, {
        status: xhr.status,
        ...xhr.response.body
    });
};

type CustomFetchFactoryDeps = {
    onProgressCallback: UploadProgressTracker['setProgress'];
    onError: () => void;
};

export type TFetchType = (deps: CustomFetchFactoryDeps) => BadgerCustomFetch;

export const fetchWithTrackingOfUploadProgressFactory: TFetchType =
    ({ onProgressCallback, onError }) =>
    (url, { method, body, headers }) => {
        return new Promise<Response>((resolve) => {
            const xhr = new XMLHttpRequest();
            xhr.open(method, url, true);

            for (const [key, value] of Object.entries(headers)) {
                xhr.setRequestHeader(key, value);
            }

            xhr.upload.onprogress = ({ loaded, total, lengthComputable }) => {
                if (lengthComputable) {
                    onProgressCallback(calculateProgress(loaded, total));
                }
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(
                        new Response(xhr.responseText, {
                            status: xhr.status,
                            statusText: xhr.statusText
                        })
                    );
                } else {
                    handleUploadFailed(xhr, onError);
                }
            };

            xhr.onerror = () => {
                handleUploadFailed(xhr, onError);
            };

            xhr.send(body as FormData);
        });
    };
