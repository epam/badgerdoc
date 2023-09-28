// temporary_disabled_rules
/* eslint-disable react-hooks/rules-of-hooks */
import { BondToDatasetResponse } from 'api/typings/bonds';
import { useBadgerFetch } from './api';

const namespace = process.env.REACT_APP_FILEMANAGEMENT_API_NAMESPACE;

// bond files to datasets
export const bondToDataset = async (
    name: string,
    objects: number[]
): Promise<BondToDatasetResponse> => {
    return useBadgerFetch<BondToDatasetResponse>({
        url: `${namespace}/datasets/bonds`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify({ name, objects }));
};
