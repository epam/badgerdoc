import { ApiTask } from '../typings/tasks';

const N = 5;
const tasksInProgress: ApiTask[] = [...Array(N)].map((_, index) => {
    return {
        id: index + 1,
        status: 'In Progress',
        file: {
            id: index + 1,
            name: `test_file_1.pdf`
        },
        pages: [1],
        job: {
            id: index + 1,
            name: `job_${index + 1}`
        },
        user: { id: '02336646-f5d0-4670-b111-c140a3ad58b5', name: 'admin' },
        is_validation: true,
        deadline: `2021-12-11T17:38:36.939Z`
    };
});

const tasksReady: ApiTask[] = [...Array(N)].map((_, index) => {
    return {
        id: index + 10,
        status: 'Ready',
        file: {
            id: index + 1,
            name: `test_file_1.pdf`
        },
        pages: [1, 1],
        job: {
            id: index + 1,
            name: `job_${index + 1}`
        },
        user: { id: '02336646-f5d0-4670-b111-c140a3ad58b5', name: 'bee' },
        is_validation: true,
        deadline: `2021-12-12T17:38:36.939Z`
    };
});

const tasksFinish: ApiTask[] = [...Array(N)].map((_, index) => {
    return {
        id: index + 100,
        status: 'Finished',
        file: {
            id: index + 1,
            name: `test_file_1.pdf`
        },
        pages: [1, 1, 1],
        job: {
            id: index + 1,
            name: `job_${index + 1}`
        },
        user: { id: '02336646-f5d0-4670-b111-c140a3ad58b5', name: 'cat' },
        is_validation: true,
        deadline: `2021-12-13T17:38:36.939Z`
    };
});

const tasksPending: ApiTask[] = [...Array(N)].map((_, index) => {
    return {
        id: index + 1000,
        status: 'Pending',
        file: {
            id: index + 1,
            name: `test_file_1.pdf`
        },
        pages: [1, 1, 1, 1],
        job: {
            id: index + 1,
            name: `job_${index + 1}`
        },
        user: { id: '02336646-f5d0-4670-b111-c140a3ad58b5', name: 'dog' },
        is_validation: false,
        deadline: `2021-12-14T17:38:36.939Z`
    };
});

export const tasks = [...tasksInProgress, ...tasksReady, ...tasksFinish, ...tasksPending];
