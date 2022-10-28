import { Pipeline, Step } from 'api/typings';
const steps1: Step[] = [
    {
        id: 'step_1',
        model: 'ternary',
        model_url: 'ternary',
        categories: ['1'],
        steps: [
            {
                id: 'step_2',
                model: '2',
                model_url: '2',
                version: 1,
                categories: ['1'],
                steps: []
            }
        ],
        version: 1
    },

    {
        id: 'step_3',
        model: '3',
        model_url: '3',
        categories: ['2'],
        steps: [],
        version: 2
    }
];
export const pipelines: Pipeline[] = [
    {
        id: 1,
        name: 'pipeline1',
        steps: steps1,
        meta: {
            categories: ['1', '2']
        }
    },
    { id: 2, name: 'pipeline2', steps: [] },
    { id: 3, name: 'pipeline3', steps: [] }
];
