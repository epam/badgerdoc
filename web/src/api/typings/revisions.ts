export type DocumentJobRevisions = {
    revision: string;
    user: string;
    pipeline: any;
    date: string;
    file_id: number;
    job_id: number;
    pages: any;
    validated: any[];
    tenant: string;
};

export type DocumentJobRevisionsResponse = DocumentJobRevisions[];
