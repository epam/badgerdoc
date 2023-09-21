import { useTokens } from 'api/hooks/tokens';
import { PageInfo } from 'api/typings';
import { useEffect, useState } from 'react';
import { TTokensFullLoadingParams } from './types';

const PAGE_TOKENS_CHUNK_SIZE = 5;

export const useTokensFullLoading = (
    { pageNumbers, task, fileMetaInfo }: TTokensFullLoadingParams,
    { enabled: hookEnabled }: { enabled: boolean }
) => {
    const [tokenPages, setTokenPages] = useState<PageInfo[]>([]);
    const [tokenPagesChunk, setTokenPagesChunk] = useState<number>(0);
    const getFileId = () => (task ? task.file.id : fileMetaInfo?.id);

    const tokenRes = useTokens(
        {
            fileId: getFileId(),
            pageNumbers: pageNumbers.slice(
                tokenPagesChunk,
                tokenPagesChunk + PAGE_TOKENS_CHUNK_SIZE
            )
        },
        { enabled: hookEnabled && tokenPagesChunk < pageNumbers.length }
    );

    useEffect(() => {
        if (hookEnabled && tokenRes.status === 'success') {
            if (tokenRes.data.length > 0 && tokenPagesChunk < pageNumbers.length) {
                setTokenPages((prevTokenPages) => [...prevTokenPages, ...tokenRes.data]);
                setTokenPagesChunk(
                    (prevTokenPagesChunk) => prevTokenPagesChunk + PAGE_TOKENS_CHUNK_SIZE
                );
            }
        }
    }, [hookEnabled, pageNumbers.length, tokenPagesChunk, tokenRes]);

    return { tokenRes, tokenPages };
};
