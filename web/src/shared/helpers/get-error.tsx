import { ApiCallError } from '@epam/uui';

export const getError = (error: any) => {
    const apiCallError = error as ApiCallError;
    let errorMessage = 'Error occurred';
    if (apiCallError.call?.responseData) {
        const responseData = error.call.responseData as any;
        errorMessage = responseData.errorMessage || responseData?.detail;
    }
    return errorMessage;
};
