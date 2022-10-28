import { QueryHookType, PageInfo } from 'api/typings';
import { useQuery } from 'react-query';
import { useBadgerFetch } from './api';

type TokensParams = {
    fileId?: number;
    pageNumbers?: number[];
};
const namespace = process.env.REACT_APP_TOKENS_API_NAMESPACE;

export const useTokens: QueryHookType<TokensParams, PageInfo[]> = (
    { fileId, pageNumbers },
    options
) => {
    return useQuery(
        ['tokens', fileId, pageNumbers],
        async () => fetchTokens(fileId, pageNumbers),
        options
    );
};

async function fetchTokens(fileId?: number, pageNumbers?: number[]): Promise<any> {
    const pageNums = pageNumbers?.map((pageNumber) => `page_numbers=${pageNumber}`);
    return useBadgerFetch({
        url: `${namespace}/tokens/${fileId}?${pageNums?.join('&')}`,
        method: 'get'
    })();
}
