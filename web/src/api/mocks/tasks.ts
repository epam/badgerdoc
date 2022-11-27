import { Task } from '../typings/tasks';
export const tasks: Task[] = [
    {
        id: 1,
        status: 'In Progress',
        file: {
            id: 1,
            name: 'test_file_1.pdf'
        },
        pages: [1],
        job: {
            id: 1,
            name: 'job_1'
        },
        user_id: '02336646-f5d0-4670-b111-c140a3ad58b5',
        is_validation: false,
        deadline: '2021-12-22T17:38:36.939Z'
    },

    {
        id: 3,
        status: 'In Progress',
        file: {
            id: 1,
            name: 'test_file_1.pdf'
        },
        pages: [1],
        job: {
            id: 3,
            name: 'job_3'
        },
        user_id: '02336646-f5d0-4670-b111-c140a3ad58b5',
        is_validation: false,
        deadline: '2021-12-22T17:38:36.939Z'
    }
];
