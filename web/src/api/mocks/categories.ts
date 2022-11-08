import { Category } from 'api/typings';

export const categories: Category[] = [
    {
        id: '1',
        name: 'category1',
        metadata: { color: '#1b67b3' },
        parent: null,
        children: ['2', '3'],
        type: 'box'
    },
    {
        id: '2',
        name: 'category2',
        metadata: { color: '#fa0808' },
        parent: '1',
        children: ['5', '6'],
        parents: [
            {
                id: '1',
                name: 'category1',
                metadata: { color: '#1b67b3' },
                parent: null,
                children: ['2', '3']
            }
        ],
        type: 'box'
    },
    {
        id: '3',
        name: 'category3',
        metadata: { color: '#313136' },
        parent: '1',
        children: null,
        parents: [
            {
                id: '1',
                name: 'category1',
                metadata: { color: '#1b67b3' },
                parent: null,
                children: ['2', '3']
            }
        ],
        type: 'box'
    },
    { id: '4', name: 'category4', metadata: { color: '#313136' }, parent: null, children: null },
    {
        id: '5',
        name: 'category5',
        metadata: { color: '#313136' },
        parent: '2',
        children: null,
        parents: [
            {
                id: '2',
                name: 'category2',
                metadata: { color: '#fa0808' },
                parent: '1',
                children: ['5', '6'],
                parents: [
                    {
                        id: '1',
                        name: 'category1',
                        metadata: { color: '#1b67b3' },
                        parent: null,
                        children: ['2', '3']
                    }
                ],
                type: 'box'
            },
            {
                id: '1',
                name: 'category1',
                metadata: { color: '#1b67b3' },
                parent: null,
                children: ['2', '3']
            }
        ],
        type: 'box'
    },
    {
        id: '6',
        name: 'category6',
        metadata: { color: '#313136' },
        parent: '2',
        children: null,
        parents: [
            {
                id: '2',
                name: 'category2',
                metadata: { color: '#fa0808' },
                parent: '1',
                children: ['5', '6'],
                type: 'box',
                parents: [
                    {
                        id: '1',
                        name: 'category1',
                        metadata: { color: '#1b67b3' },
                        parent: null,
                        children: ['2', '3']
                    }
                ]
            },
            {
                id: '1',
                name: 'category1',
                metadata: { color: '#1b67b3' },
                parent: null,
                children: ['2', '3'],
                type: 'box'
            }
        ]
    },
    {
        id: '7',
        name: 'category6',
        metadata: { color: '#313136' },
        parent: null,
        children: null,
        type: 'box'
    },
    {
        id: '8',
        name: 'category6',
        metadata: { color: '#313136' },
        parent: null,
        children: null,
        type: 'box'
    },
    {
        id: '9',
        name: 'category6',
        metadata: { color: '#313136' },
        parent: null,
        children: null,
        type: 'box'
    },
    {
        id: '10',
        name: 'category6',
        metadata: { color: '#313136' },
        parent: null,
        children: null,
        type: 'box'
    },
    {
        id: '11',
        name: 'category6',
        metadata: { color: '#313136' },
        parent: null,
        children: null,
        type: 'box'
    },
    {
        id: '12',
        name: 'category6',
        metadata: { color: '#313136' },
        parent: null,
        children: null,
        type: 'box'
    },
    {
        id: '13',
        name: 'category6',
        metadata: { color: '#313136' },
        parent: null,
        children: null,
        type: 'box'
    },
    {
        id: '14',
        name: 'category6',
        metadata: { color: '#313136' },
        parent: null,
        children: null,
        type: 'link'
    },
    {
        id: '15',
        name: 'category6',
        metadata: { color: '#313136' },
        parent: null,
        children: null,
        type: 'link'
    },
    {
        id: '16',
        name: 'category6',
        metadata: { color: '#313136' },
        parent: null,
        children: null,
        type: 'link'
    }
];
