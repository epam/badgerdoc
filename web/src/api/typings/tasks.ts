export type Task = {
    id: number;
    status: TaskStatus;
    file: {
        name: string;
        id: number;
    };
    pages: number[];
    job: {
        name: string;
        id: number;
    };
    user_id: string;
    is_validation: boolean;
    deadline: string;
};

export type DistributeTasksResponse = Task[];

// all properties are optional due to form validation
export type TaskModel = {
    file_id: number;
    pages: Array<number>;
    job_id: number;
    //todo: add dependecy from other models
    user_id: string;
    is_validation: boolean;
    deadline: string;
};
export type ValidationPages = {
    validated: [];
    failed_validation_pages: [];
    annotated_pages: [];
    not_processed: [];
};

export type TaskStatus = 'Pending' | 'Ready' | 'In Progress' | 'Finished';

export type ValidationPageStatus = 'Valid Page' | 'Invalid Page';
