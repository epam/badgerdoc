import { ApiCallError } from '@epam/uui';

enum DETAIL {
    STRING = 'string',
    OBJECT = 'object',
    ARRAY = 'array'
}

const DEFAULT_ERROR_MESSAGE = 'Error occurred';

export const getError = (error: any) => {
    try {
        const apiCallError = error as ApiCallError;
        let errorMessage = DEFAULT_ERROR_MESSAGE;

        if (apiCallError.call?.responseData) {
            const responseData = error.call.responseData as any;
            errorMessage = responseData.errorMessage || responseData?.detail;
        } else if (error.details.detail) {
            const detailType = extractDetailType(error.details.detail);

            switch (detailType) {
                case DETAIL.STRING:
                    return error.details.detail;
                case DETAIL.OBJECT:
                    return error.details.detail.msg;
                case DETAIL.ARRAY:
                    return error.details.detail[0].msg;
                default:
                    return proceedUnhandledType(detailType);
            }
        }

        return errorMessage;
    } catch (e) {
        console.error('Something went wrong', e);

        return DEFAULT_ERROR_MESSAGE;
    }
};

const extractDetailType = (detail: any) => {
    return Array.isArray(detail) ? DETAIL.ARRAY : typeof detail;
};

const proceedUnhandledType = (dataType: string) => {
    throw new Error(`Unhandled type was used: ${dataType}`);
};
