import { FileDocument } from 'api/typings';

export const W2: FileDocument = {
    id: 1,
    original_name: 'W2 form for tax returns',
    bucket: '???',
    size_in_bytes: 100500,
    content_type: '???',
    last_modified: new Date(Date.parse('10/1/2021')).toString(),
    datasets: ['1'],
    status: 'Processed',
    pages: 100,
    extension: '.pdf',
    path: ''
};

export const documents = [W2];
