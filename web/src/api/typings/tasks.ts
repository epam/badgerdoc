export type ApiTask = {
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
    user: {
        id: string;
        name: string;
    };
    is_validation: boolean;
    deadline: string;
};

export type Task = Omit<ApiTask, 'user'> & {
    user_id: string;
};

export type DistributeTasksResponse = Task[];

// all properties are optional due to form validation
export type TaskModel = {
    id: number;
    file_id: number;
    pages: Array<number>;
    job_id: number;
    //todo: add dependency from other models
    user_id: string;
    is_validation: boolean;
    deadline: string;
    status: string;
};
export type ValidationPages = {
    validated: [];
    failed_validation_pages: [];
    annotated_pages: [];
    not_processed: [];
};

export type TaskStats = {
    event_type: 'opened' | 'closed';
    additional_data: { [key in string]: string };
    task_id: number;
    created: string;
    updated: string;
};

export type TaskStatus = 'Pending' | 'Ready' | 'In Progress' | 'Finished';

export type ValidationPageStatus = 'Valid Page' | 'Invalid Page';
