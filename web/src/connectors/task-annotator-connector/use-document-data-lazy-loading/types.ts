import { Job } from 'api/typings/jobs';
import { Task } from 'api/typings/tasks';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';
import { Dispatch, SetStateAction } from 'react';
import { Annotation } from 'shared';

export type TRange = {
    begin: number;
    end: number;
};

export type TDocumentDataLazyLoadingParams = {
    task?: Task;
    job?: Job;
    jobId?: number;
    fileMetaInfo?: FileMetaInfo;
    revisionId?: string;
    pageNumbers: number[];
    setSelectedAnnotation: Dispatch<SetStateAction<Annotation | undefined>>;
};

export type TAnnotationsLazyLoadingParams = TDocumentDataLazyLoadingParams & {
    availableRenderedPagesRange: TRange;
    nextLoadingPagesRange: TRange;
    nextLoadingPageNumbers: number[];
};

export type TTokensLazyLoadingParams = Pick<
    TDocumentDataLazyLoadingParams,
    'task' | 'fileMetaInfo' | 'pageNumbers'
> & {
    availableRenderedPagesRange: TRange;
    nextLoadingPagesRange: TRange;
    nextLoadingPageNumbers: number[];
};
