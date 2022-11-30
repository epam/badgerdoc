import { UseMutationResult, UseQueryOptions, UseQueryResult } from 'react-query';
import { UseInfiniteQueryResult } from 'react-query/types/react/types';
import { ModelStatus } from 'api/typings/models';
import { Task } from './typings/tasks';
import React from 'react';

export type Credentials = {
    username: string;
    password: string;
};

export type AuthResult = {
    jwt: string | null;
    tenants: string[];
    expiresIn: number;
};

export type StoredAuthResult = {
    authResult?: AuthResult;
    updateAtTimestamp: number;
    refreshInterval: number;
};

export type AuthResultRaw = {
    access_token: string;
    expires_in: number;
};

type SSOProvider = {
    'Auth link': string;
    Alias: string;
};

export type AuthProviderRaw = {
    'Identity Providers Info': Array<SSOProvider>;
};

export type FileDocument = {
    id: number;
    original_name: string;
    bucket: string;
    size_in_bytes: number;
    extension: string;
    content_type: string;
    pages: number;
    last_modified: string;
    status: string;
    path: string;
    datasets: Dataset['name'][];
};
export type PagedResponse<T> = {
    data: T[];
    pagination: {
        has_more: boolean;
        min_pages_left: number;
        page_num: number;
        page_size: number;
        total: number;
    };
};

export type Dataset = {
    count: number;
    created: string;
    id: number;
    name: string;
    // files: string[];
};

export type Preprocessor = {
    modelId: string;
    name: string;
};
export type PipelineTypes = 'preprocessing' | 'inference';
export type PipelineData = {
    name: string;
    steps?: Step[];
    meta?: {
        name?: string;
        categories: string[];
        original_pipeline_id?: number;
        type?: PipelineTypes;
        description?: string;
        summary?: string;
    };
    label?: string;
    model?: string;
    version?: number;
};
export type Pipeline = PipelineData & {
    id: number;
    original_pipeline_id?: number;
    summary?: string;
    type?: string;
    description?: string;
    is_latest?: boolean;
};

export type Step = {
    id: string;
    model: string;
    version: number | null;
    model_url: string;
    steps?: Step[];
    categories?: string[];
    args?: Record<string, string>;
};
export type Model = {
    description?: string;
    id: string;
    name: string;
    basement?: string;
    data_path?: {
        file: string;
        bucket: string;
    };
    configuration_path?: {
        file: string;
        bucket: string;
    };
    training_id?: number;
    score?: number;
    categories?: string[];
    type?: string;
    status?: ModelStatus;
    created_by?: string;
    created_at?: string;
    tenant?: string;
    version?: number;
    latest?: boolean;
    parentId?: string;
};

export type Training = {
    name: string;
    jobs?: number[];
    basement?: string;
    epochs_count?: number;
    kuberflow_pipeline_id?: string;
    id: number;
    created_at?: string;
    created_by?: string;
    tenant?: string;
};

export type ModelDeployment = {
    apiVersion?: string;
    datetime_creation?: string;
    model_id: number;
    model_name: string;
    status: string;
    reason?: string;
    message?: string;
    namespace?: string;
    resourceVersion?: string;
    uuid?: string;
    image?: string;
    container_name?: string;
    url?: string;
};

export type CategoryDataAttrType = 'molecule' | 'latex' | 'text' | 'taxonomy' | '';

export type CategoryDataAttribute = {
    name: string;
    type: CategoryDataAttrType;
};

export type CategoryDataAttributeWithValue = {
    name: string;
    type: CategoryDataAttrType;
    value: string;
};

export type ExternalViewerState = {
    isOpen: boolean;
    type: CategoryDataAttrType;
    name: string;
    value: string;
};

export type SupportedArgs = {
    name: string;
    type?: string;
    multiple?: boolean;
    required?: boolean;
};
export type Basement = {
    id: string;
    name: string;
    supported_args?: SupportedArgs[] | null;
    gpu_support?: boolean;
    created_by?: string;
    created_at?: string;
    tenant?: string;
};

export const categoryTypes = ['box', 'link', 'segmentation'] as const;
export type CategoryType = typeof categoryTypes[number];

export interface BaseCategory {
    id: string;
    name: string;
    parent: string | null;
    metadata?: {
        color: string;
    };
    type?: CategoryType;
    data_attributes?: Array<CategoryDataAttribute> | null;
    isLeaf: boolean;
}

export interface Category extends BaseCategory {
    is_link?: boolean;
    hotkey?: string;
    parents?: BaseCategory[] | null;
}

export interface TreeNode {
    title: string;
    key: string;
    isLeaf: boolean;
    children: CategoryNode[];
}
export interface CategoryNode extends TreeNode {
    category?: BaseCategory;
    hotKey?: string;
    style?: React.CSSProperties;
}

export interface TaxonomyNode extends TreeNode {
    dataAttributes?: string;
    taxon?: BaseTaxon;
}

export interface BaseTaxon {
    id: string;
    name: string;
    parent_id: string | null;
    is_leaf: boolean;
    taxonomy_id: string;
}

export interface Taxon extends BaseTaxon {
    parents?: BaseTaxon[];
}
export interface Taxonomy {
    id: string;
    name: string;
    taxons: BaseTaxon[];
}
export type Link = {
    category_id: string;
    to: string | number;
    type: 'directional' | 'undirectional' | 'omnidirectional';
    page_num: number; // optional if different page
};

export type CreateCategory = {
    id: string;
    name: string;
    metadata: {
        color: string;
    };
    parent: string | null;
    type: CategoryType;
};

export type UpdateCategory = {
    id: string;
    name: string;
    metadata: {
        color: string;
    };
    parent: string | null;
    type: CategoryType;
    data_attributes: Array<CategoryDataAttribute>;
};

export type User = {
    tenants: Array<string>;
    id: string;
    user_id: string;
    username: string;
    // custom field, not in API
    current_tenant?: string;
    realm_access: {
        roles: string[];
    };
};

export type DatasetResponse = {
    id: number;
    name: string;
    created: string;
    files: string[];
};

/**
 * P - params type
 * RT - return type
 * */
export type QueryHookType<PT, RT> = (
    params: PT,
    options?: UseQueryOptions<RT, any, RT>
) => UseQueryResult<RT>;

export type QueryInfiniteHookType<PT, RT> = (
    params: PT,
    options: UseQueryOptions<RT, any, RT>
) => UseInfiniteQueryResult<RT>;

export type QueryHookParamsType<T> = {
    page: number;
    size: number;
    tenant?: string;
    searchText: string;
    sortConfig: {
        field: keyof T;
        direction: SortingDirection;
    };
    filters?: Array<Filter<keyof T>>;
};

export type MutationHookType<PT, RT> = () => UseMutationResult<RT, any, PT>;

export type AnnotationJob = {
    name: string;
    datasets: Dataset[];
    users: string[];
    files: File[];
    validators: string[];
    labels: string[];
};

export type ExtractionJob = {
    name: string;
    datasets: Dataset[];
    files: File[];
    pipeline_name: string;
};

export type Pagination = Record<'page_num' | 'page_size', number>;
export enum Operators {
    IS_NULL = 'is_null',
    IS_NOT_NULL = 'is_not_null',
    EQ = 'eq',
    NE = 'ne',
    GT = 'gt',
    LT = 'lt',
    GE = 'ge',
    LE = 'le',
    LIKE = 'like',
    ILIKE = 'ilike',
    NOT_LIKE = 'not_like',
    IN = 'in',
    NOT_IN = 'not_in',
    ANY = 'any',
    NOT_ANY = 'not_any',
    MATCH = 'match',
    DISTINCT = 'distinct',
    CHILDREN = 'children'
}
export type DocumentExtraOption = {
    'datasets.id': string;
    'datasets.name': string;
};
export type Filter<TField> = {
    field: TField | keyof DocumentExtraOption;
    operator: Operators;
    value?: string | Array<string> | number | Array<number> | boolean | Array<boolean>;
};
export enum SortingDirection {
    ASC = 'asc',
    DESC = 'desc'
}
export type Sorting<TField> = {
    field: TField;
    direction: SortingDirection;
};
export type SearchBody<TItem> = {
    pagination: Pagination;
    filters: Filter<keyof TItem | string>[];
    sorting: Sorting<keyof TItem>[];
};

export type ValidationType = 'cross' | 'hierarchical' | 'validation only';

export type PageInfoObjs = {
    id?: number;
    type?: string;
    bbox: number[];
    category?: number | string;
    text?: string;
    data?: any;
    links?: Link[];
    children?: number[] | string[];
    segments?: number[][];
};
export type PageInfo = {
    size?: { width: number; height: number };
    page_num: number;
    objs: PageInfoObjs[];
};

export type ResponseError = {
    statusText: string;
    details: Record<string, unknown>;
    message: string;
};

export type TableFilters<TItem, TValues = []> = {
    [key in keyof TItem]?: {
        [key in Operators]?: TValues | string[];
    };
};

export type HTTPRequestMethod = 'post' | 'get' | 'delete' | 'put';

export type UseTasksResponseObj = {
    current_page: number;
    page_size: number;
    total_objects: number;
    annotation_tasks: Task[];
};

export type Language = {
    id: string;
    name: string;
};

export type PagingCache<T> = {
    page: number;
    cache: Array<T>;
    search: string;
};

export type PagingFetcher<T> = (
    page: number,
    size: number,
    keyword?: string
) => Promise<PagedResponse<T>>;

export type DocumentView = 'table' | 'card';
