import { PageInfoObjs } from 'api/typings';
import { PageToken } from 'shared';

export const createTextFromToken = (token: PageInfoObjs | PageToken) => {
    const previousSymbol = token?.previous || '';
    const afterSymbol = token?.after || '';
    const text = token?.text || '';
    return previousSymbol + text + afterSymbol;
};
