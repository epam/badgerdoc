import { BadgerCustomFetch } from 'api/hooks/api';
import { UploadProgressTracker } from './use-fetch-with-tracking-of-upload-progress';
import { ApiError } from 'api/api-error';

const calculateProgress = (loaded: number, total: number): number => {
    return Math.floor(100 * (loaded / total));
};

type CustomFetchFactoryDeps = {
    onProgressCallback: UploadProgressTracker['setProgress'];
    onError: () => void;
};

export type TFetchType = (deps: CustomFetchFactoryDeps) => BadgerCustomFetch;

export const fetchWithTrackingOfUploadProgressFactory: TFetchType =
    ({ onProgressCallback, onError }) =>
    async (url, { method, body, headers }) => {
        let response = {} as Response;
        try {
            response = await new Promise<Response>((resolve, reject) => {
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
                    }
                };

                xhr.onerror = () => {
                    reject(
                        new ApiError(xhr.statusText, `Upload failed with status ${xhr.status}`, {
                            status: xhr.status,
                            ...xhr.response.body
                        })
                    );
                };

                xhr.send(body as FormData);
            });
        } catch (error) {
            onError();
            response = { status: 500, statusText: 'Upload failed!' } as Response;
        } finally {
            // eslint-disable-next-line no-unsafe-finally
            return response;
        }
    };
