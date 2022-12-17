import { HTTPRequestMethod, Report } from 'api/typings';
import { useBadgerFetch } from './api';

export async function fetchReport(
    url: string,
    method: HTTPRequestMethod,
    body: Report
): Promise<Blob> {
    return useBadgerFetch<Blob>({
        url,
        method,
        withCredentials: true,
        isBlob: true
    })(JSON.stringify(body));
}
