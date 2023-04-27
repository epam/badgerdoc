import { CategoryDataAttrType } from '../../api/typings';
import { PageSize } from '../../shared/components/document-pages/document-pages';

interface Token {
    id: number;
    text: string;
    x: number;
    y: number;
    width: number;
    height: number;
}

interface Data {
    tokens: Token[];
    dataAttributes: CategoryDataAttrType[];
}

interface PageInfoObj {
    id: number;
    type: string;
    bbox: number[];
    category: string;
    data: Data;
    children: number[];
    text: string;
}

interface Page {
    page_num: number;
    size: PageSize;
    objs: PageInfoObj[];
    revision: string;
    user_id: string;
    pipeline: number;
    date: string;
    is_validated: boolean;
    categories: string[];
}

export interface LatestRevisionObj {
    [page_num: string]: Page[];
}

export interface RevisionObjByUser {
    [user_id: string]: {
        [page_num: number]: {
            size: PageSize;
            objs: PageInfoObj[];
        };
    };
}

export interface UserRevision {
    user_id: string;
    page_num: number;
    size: PageSize;
    objs: PageInfoObj[];
    revision: string;
    isValidated: boolean;
    date: string;
    pipeline: number;
    categories: string[];
}

export function convertToRevisionByUserArray(sourceObj: LatestRevisionObj): UserRevision[] {
    const userRevisions: UserRevision[] = [];

    for (const page_num in sourceObj) {
        const pages = sourceObj[page_num];

        for (const page of pages) {
            const {
                user_id: user_id,
                size,
                objs,
                revision,
                is_validated,
                date,
                pipeline,
                categories
            } = page;

            userRevisions.push({
                user_id,
                page_num: parseInt(page_num),
                size,
                objs,
                revision,
                isValidated: is_validated,
                date,
                pipeline,
                categories
            });
        }
    }

    return userRevisions;
}

export function delAllRevisionByUser(
    sourceObj: RevisionObjByUser,
    user_id?: string
): RevisionObjByUser {
    if (!user_id) return sourceObj;

    const result: RevisionObjByUser = {};

    for (const key in sourceObj) {
        if (key !== user_id) {
            result[key] = sourceObj[key];
        }
    }

    return result;
}

export function getRevisionByUser(
    sourceObj: RevisionObjByUser,
    user_id?: string
): RevisionObjByUser {
    if (!user_id) return {};
    const result: RevisionObjByUser = {};

    if (user_id in sourceObj) {
        result[user_id] = sourceObj[user_id];
    }

    return result;
}
