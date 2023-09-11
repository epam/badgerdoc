import { Job } from 'api/typings/jobs';
import { Task } from 'api/typings/tasks';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';

export type TDocumentDataFullLoadingParams = {
    task?: Task;
    job?: Job;
    jobId?: number;
    fileMetaInfo?: FileMetaInfo;
    revisionId?: string;
    pageNumbers: number[];
};

export type TTokensFullLoadingParams = Pick<
    TDocumentDataFullLoadingParams,
    'task' | 'fileMetaInfo' | 'pageNumbers'
>;
