import { UploadIndicatorContextType } from 'components/upload-indicator/upload-indicator.context';

const calculateProgress = (loaded: number, total: number): number => {
    return Math.floor(100 * (loaded / total));
};

export const trackUploadProgress = (
    url: string,
    method: string,
    uploadIndicatorContext?: UploadIndicatorContextType,
    body?: FormData,
    headers?: Record<string, string> | Headers
): Promise<Response> => {
    return new Promise<Response>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open(method, url, true);

        if (headers) {
            for (const [key, value] of Object.entries(headers)) {
                xhr.setRequestHeader(key, value);
            }
        }

        xhr.upload.onprogress = ({ loaded, total, lengthComputable }) => {
            if (lengthComputable && uploadIndicatorContext) {
                uploadIndicatorContext.setProgress(calculateProgress(loaded, total));
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
                uploadIndicatorContext?.setProgress(0);
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
