import { ApiTask } from '../typings/tasks';

const N = 150;
export const tasks: ApiTask[] = [...Array(N)].map((_, index) => {
    return {
        id: index + 1,
        status: 'In Progress',
        file: {
            id: index + 1,
            name: `test_file_${index + 1}.pdf`
        },
        pages: [1],
        job: {
            id: index + 1,
            name: `job_${index + 1}`
        },
        user: { id: '02336646-f5d0-4670-b111-c140a3ad58b5', name: 'admin' },
        is_validation: true,
        deadline: '2021-12-22T17:38:36.939Z'
    };
});
