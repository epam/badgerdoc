import { ValidationType } from '../typings';

export type DocumentJob = {
    id: number;
    files: string[];
    deadline: string;
    datasets: any[];
    creation_datetime: string;
    categories: string[];
    is_auto_distribution: boolean;
    name: string;
    status: string;
    type: string;
    users: string[];
    mode?: string;
};

export type DocumentJobsResponse = DocumentJob[];

export type JobMode = 'Manual' | 'Automatic';

export type Job = {
    id: number;
    name: string;
    // TODO: create enum or type with defined value
    status?: JobStatus;
    files: Array<number>;
    // TODO: assumption - list of ids
    datasets: string[];
    creation_datetime: string;
    // TODO: create enum or type with defined value
    type: JobType;
    // TODO: create enum or type with defined value
    mode: JobMode;
    pipeline_id: string;
    annotators: Array<string>;
    validators: Array<string>;
    owners: Array<string>;
    categories: Array<number>;
    is_auto_distribution: boolean;
    deadline?: string;
    // TODO: create enum or type with defined value
    validation_type: ValidationType;
    // TODO: check pipeline property
};

export type JobType =
    | 'ExtractionWithAnnotationJob'
    | 'AnnotationJob'
    | 'ExtractionJob'
    | 'ImportJob';

export type JobStatus =
    | 'Pending'
    | 'In Progress'
    | 'Failed'
    | 'Finished'
    | 'Draft'
    | 'Ready For Annotation';
