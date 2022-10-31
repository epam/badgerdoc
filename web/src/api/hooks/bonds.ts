import { BondToDatasetReponse } from 'api/typings/bonds';
import { useBadgerFetch } from './api';

const namespace = process.env.REACT_APP_FILEMANAGEMENT_API_NAMESPACE;

// bond files to datasets
export const bondToDataset = async (
    name: string,
    objects: Array<number>
): Promise<BondToDatasetReponse> => {
    return useBadgerFetch<BondToDatasetReponse>({
        url: `${namespace}/datasets/bonds`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify({ name, objects }));
};
