import { Model } from 'api/typings';

export const models: Model[] = [
    {
        id: 'ternary',
        name: 'ternary',
        basement: 'badgerdoc/ternary_classifier:0.1.1-c20f0295',
        data_path: {
            file: 'export.pkl',
            bucket: 'annotation'
        },
        configuration_path: {
            file: 'ternarytest.txt',
            bucket: 'annotation'
        },

        categories: ['molecule', 'chart', 'not_chart'],
        status: 'deployed',
        created_by: '901',
        created_at: '2021-12-14T07:53:39.413731',
        tenant: 'epam'
    },
    {
        id: 'table-post',
        name: 'table-post',
        basement: 'badgerdoc/table_extractor_postprocessing:0.1.1-5d46b950',
        data_path: {
            file: 'tokenizer.pth',
            bucket: 'annotation'
        },
        configuration_path: {
            file: 'training_meta.json',
            bucket: 'annotation'
        },

        categories: ['cell', 'header', 'table'],

        status: 'deployed',
        created_by: '901',
        created_at: '2022-01-14T07:07:08.794520',
        tenant: 'test'
    },
    {
        id: 'table',
        name: 'table',
        basement: 'badgerdoc/table_extractor_inference:0.1.2-32c0d82f',
        data_path: {
            file: 'table.pth',
            bucket: 'config'
        },
        configuration_path: {
            file: 'table.py',
            bucket: 'config'
        },
        categories: ['table', 'Cell', 'header'],
        status: 'deployed',
        created_by: '901',
        created_at: '2021-12-22T07:06:07.424622',
        tenant: 'epam'
    }
];
