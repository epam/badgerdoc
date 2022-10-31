import { AnotationsResponse } from 'api/hooks/annotations';

export const annotations: AnotationsResponse = {
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
                    id: 1642342666611,
                    type: 'box',
                    bbox: [75, 82, 537, 119],
                    category: 1
                },
                {
                    id: 1642343157986,
                    type: 'box',
                    bbox: [53, 266, 295, 487],
                    category: 2
                },
                {
                    id: 1642343249912,
                    type: 'box',
                    bbox: [317, 406, 558, 447],
                    category: 3
                }
            ]
        }
    ],
    validated: [],
    failed_validation_pages: []
};
