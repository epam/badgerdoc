export type UseFacetsParamsType = {
    query: string;
    categoryLimit: number;
    jobLimit: number;
    categoryFilter: string[];
    jobFilter: string[];
};

export type FacetName = 'category' | 'job_id';

export type FacetValue = {
    id: string;
    count: number;
    name?: string;
};

export type Facets = {
    name: FacetName;
    values: FacetValue[];
};

export type FacetsBodyLimit = {
    name: FacetName;
    limit?: number;
};

export type FacetsBodyFilters = {
    field: FacetName;
    operator: 'in';
    value: string[];
};

export type FacetsBody = {
    facets: FacetsBodyLimit[];
    query?: string;
    filters?: FacetsBodyFilters[];
};

export type FacetsResponse = {
    facets: Facets[];
};

export type FacetValuesFilter = {
    id: string;
    value: boolean;
};

export type FacetFilter = {
    category: FacetValuesFilter[];
    job_id: FacetValuesFilter[];
};

export type UsePiecesParamsType = {
    page?: number;
    size?: number;
    searchText?: string;
    sort: string;
    filter: FacetFilter;
};

export type Pieces = {
    category: string;
    content: string;
    document_id: number;
    page_number: number;
    bbox: number[];
    tokens: any;
    job_id: number;
};
