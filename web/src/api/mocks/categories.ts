import { Category } from 'api/typings';

export const categories: Category[] = [
    {
        name: 'Child1',
        parent: 'Parent',
        metadata: {
            color: '#4200ff'
        },
        type: 'box',
        data_attributes: null,
        id: 'Child1',
        parents: [
            {
                name: 'Parent',
                parent: null,
                metadata: {
                    color: '#ff0000'
                },
                type: 'box',
                data_attributes: null,
                id: 'Parent'
            }
        ],
        children: [
            {
                name: 'Child1.1',
                parent: 'Child1',
                metadata: {
                    color: '#c400ff'
                },
                type: 'box',
                data_attributes: [],
                id: 'Child1.1'
            }
        ]
    },
    {
        name: 'Child1.1',
        parent: 'Child1',
        metadata: {
            color: '#c400ff'
        },
        type: 'box',
        data_attributes: [],
        id: 'Child1.1',
        parents: [
            {
                name: 'Child1',
                parent: 'Parent',
                metadata: {
                    color: '#4200ff'
                },
                type: 'box',
                data_attributes: null,
                id: 'Child1'
            },
            {
                name: 'Parent',
                parent: null,
                metadata: {
                    color: '#ff0000'
                },
                type: 'box',
                data_attributes: null,
                id: 'Parent'
            }
        ],
        children: []
    },
    {
        name: 'Child2',
        parent: 'Parent',
        metadata: {
            color: '#006e39'
        },
        type: 'box',
        data_attributes: null,
        id: 'Child2',
        parents: [
            {
                name: 'Parent',
                parent: null,
                metadata: {
                    color: '#ff0000'
                },
                type: 'box',
                data_attributes: null,
                id: 'Parent'
            }
        ],
        children: []
    },
    {
        name: 'Parent',
        parent: null,
        metadata: {
            color: '#ff0000'
        },
        type: 'box',
        data_attributes: null,
        id: 'Parent',
        parents: [],
        children: [
            {
                name: 'Child1',
                parent: 'Parent',
                metadata: {
                    color: '#4200ff'
                },
                type: 'box',
                data_attributes: null,
                id: 'Child1'
            },
            {
                name: 'Child2',
                parent: 'Parent',
                metadata: {
                    color: '#006e39'
                },
                type: 'box',
                data_attributes: null,
                id: 'Child2'
            },
            {
                name: 'Child1.1',
                parent: 'Child1',
                metadata: {
                    color: '#c400ff'
                },
                type: 'box',
                data_attributes: [],
                id: 'Child1.1'
            }
        ]
    }
];
