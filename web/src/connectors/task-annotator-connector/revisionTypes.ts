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
        [page_num: string]: {
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
