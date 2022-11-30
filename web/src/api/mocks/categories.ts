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
                id: 'Parent',
                isLeaf: false
            }
        ],
        isLeaf: false
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
                id: 'Child1',
                isLeaf: false
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
                isLeaf: false
            }
        ],
        isLeaf: true
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
                id: 'Parent',
                isLeaf: false
            }
        ],
        isLeaf: true
    },
    {
        name: 'Parent',
        parent: null,
        metadata: {
            color: '#ff0000'
        },
        type: 'box',
        data_attributes: [
            {
                name: 'taxonomy',
                type: 'taxonomy'
            }
        ],
        id: 'Parent',
        parents: [],
        isLeaf: false
    }
];
