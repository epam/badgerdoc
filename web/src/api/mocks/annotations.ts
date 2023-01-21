import { AnnotationsResponse } from 'api/hooks/annotations';

export const annotations: AnnotationsResponse = {
    revision: 'revision-1',
    pages: [
        {
            size: {
                width: 0,
                height: 0
            },
            page_num: 1,
            objs: [
                {
                    id: 1642343157986,
                    type: 'box',
                    bbox: [53, 266, 295, 487],
                    category: 'Child2',
                    data: {
                        dataAttributes: [{ name: 'dataAttr', type: 'text', value: 'dataAttr' }]
                    }
                },
                {
                    id: 1642343249912,
                    type: 'box',
                    bbox: [317, 406, 558, 447],
                    category: 'Child1.1',
                    data: {
                        dataAttributes: [{ name: 'dataAttr', type: 'text', value: 'dataAttr' }]
                    }
                }
            ]
        }
    ],
    validated: [],
    failed_validation_pages: [],
    categories: ['taxons_id_1', 'taxons_id_2'],
    links_json: [{ to: 1, category: 'doc_link1', type: 'undirectional' }]
};
