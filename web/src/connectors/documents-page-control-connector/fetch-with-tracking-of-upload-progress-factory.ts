import { BadgerCustomFetchRequestParams } from 'api/hooks/api';
import { UploadProgressTracker } from './use-fetch-with-tracking-of-upload-progress';

const calculateProgress = (loaded: number, total: number): number => {
    return Math.floor(100 * (loaded / total));
};

export const fetchWithTrackingOfUploadProgressFactory =
    ({ uploadProgressTracker }: { uploadProgressTracker: UploadProgressTracker }) =>
    ({ url, method, body, headers }: BadgerCustomFetchRequestParams): Promise<Response> => {
        return new Promise<Response>((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open(method, url, true);

            for (const [key, value] of Object.entries(headers)) {
                xhr.setRequestHeader(key, value);
            }

            xhr.upload.onprogress = ({ loaded, total, lengthComputable }) => {
                if (lengthComputable && uploadProgressTracker) {
                    uploadProgressTracker.setProgress(calculateProgress(loaded, total));
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
                    reject(new Error(`Upload failed with status ${xhr.status}`));
                }
            };

            xhr.onerror = () => {
                reject(new Error('Upload failed'));
            };

            xhr.send(body);
        });
    };
