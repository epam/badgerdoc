// temporary_disabled_rules
/* eslint-disable react-hooks/rules-of-hooks */
import { QueryHookType } from '../typings';
import { useQuery, useQueries } from 'react-query';
import { useBadgerFetch } from './api';
import { getAuthHeaders } from 'shared/helpers/auth-tools';

const namespace = process.env.REACT_APP_FILEMANAGEMENT_API_NAMESPACE;

type FileParams = {
    fileId: number;
};
export const useAssetById: QueryHookType<FileParams, any> = ({ fileId }, options) => {
    return useQuery(['asset', fileId], async () => fetchLatestAnnotations(fileId), options);
};

async function fetchLatestAnnotations(fileId: number): Promise<any> {
    return useBadgerFetch({
        url: `${namespace}/download?file_id=${fileId}`,
        method: 'get',
        withCredentials: true,
        isBlob: true
    })();
}

export const fetchThumbnail = async (fileId: number) => {
    const combinedHeaders = {};
    Object.assign(combinedHeaders, {
        ...getAuthHeaders()
    });

    const response = await fetch(`${namespace}/download/thumbnail?file_id=${fileId}`, {
        headers: {
            ...combinedHeaders
        }
    });
    const imageBlob = await response.blob();
    return {
        fileId,
        image: URL.createObjectURL(imageBlob)
    };
};

export const useThumbnail = (filesId: number[] | undefined) => {
    if (filesId) {
        const res = {};
        const thumbnailRes = useQueries(
            filesId.map((id) => {
                return {
                    queryKey: ['thumbnail', id],
                    queryFn: () => fetchThumbnail(id),
                    refetchOnWindowFocus: false
                };
            })
        );
        thumbnailRes.forEach((thumbnail) => {
            if (thumbnail.data) {
                // @ts-ignore
                res[thumbnail.data.fileId] = thumbnail.data.image;
            }
        });
        return res;
    }
};

type ThumbnailPieceParam = {
    fileId: number;
    pageNum: number | undefined;
    bbox: number[] | undefined;
};

export const useThumbnailPiece: QueryHookType<ThumbnailPieceParam, any> = (
    { fileId, pageNum, bbox },
    options
) => {
    return useQuery(
        ['thumbnailPiece', fileId, pageNum, bbox],
        async () => fetchThumbnailPiece(fileId, pageNum, bbox),
        options
    );
};

export const fetchThumbnailPiece = async (
    fileId: number,
    pageNum: number | undefined,
    bbox: number[] | undefined
) => {
    if (pageNum && bbox) {
        const combinedHeaders = {};
        Object.assign(combinedHeaders, {
            ...getAuthHeaders()
        });

        const response = await fetch(
            `${namespace}/download/piece?file_id=${fileId}&page_number=${pageNum}${bbox
                .map((el) => `&bbox=${el}`)
                .join('')}`,
            {
                headers: {
                    ...combinedHeaders
                }
            }
        );
        const imageBlob = await response.blob();
        return URL.createObjectURL(imageBlob);
    }
};
