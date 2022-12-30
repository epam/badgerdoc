import { AnnotationsByUserResponse } from 'api/hooks/annotations';

export const annotationsByUser: AnnotationsByUserResponse = {
    '1': [
        {
            page_num: 1,
            size: {
                width: 0,
                height: 0
            },
            objs: [
                {
                    id: 1642342666611,
                    type: 'box',
                    bbox: [75, 82, 537, 119],
                    category: 'Parent',
                    data: {
                        dataAttributes: [{ name: 'dataAttr', type: 'text', value: 'dataAttr' }]
                    }
                },
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
            ],
            revision: '23d9fcf082df38f0811eb17cf125052e5e595f8a',
            user_id: '345'
        },
        {
            page_num: 1,
            size: {
                width: 0,
                height: 0
            },
            objs: [
                {
                    id: 16423426666112,
                    type: 'box',
                    bbox: [75, 82, 537, 119],
                    category: 'Child2',
                    data: {
                        dataAttributes: [{ name: 'dataAttr', type: 'text', value: 'dataAttr' }]
                    }
                },
                {
                    id: 16423431579862,
                    type: 'box',
                    bbox: [53, 266, 295, 487],
                    category: 'Child1',
                    data: {
                        dataAttributes: [{ name: 'dataAttr', type: 'text', value: 'dataAttr' }]
                    }
                },
                {
                    id: 16423432499122,
                    type: 'box',
                    bbox: [317, 406, 558, 447],
                    category: 'Parent',
                    data: {
                        dataAttributes: [{ name: 'dataAttr', type: 'text', value: 'dataAttr' }]
                    }
                }
            ],
            revision: '23d9fcf082df38f0811eb17cf125052e5e595f8a',
            user_id: '123'
        }
    ]
};
