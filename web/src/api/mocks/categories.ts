import { Category } from 'api/typings';

export const categories: Category[] = [
    {
        name: 'Category_1',
        parent: 'Parent',
        metadata: {
            color: '#4200ff'
        },
        type: 'document',
        data_attributes: null,
        id: 'Category_1_id',
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
        name: 'Category_2',
        parent: 'Parent',
        metadata: {
            color: '#4200ff'
        },
        type: 'document',
        data_attributes: [
            {
                name: 'taxonomy_id1_cat2',
                type: 'taxonomy'
            },
            {
                name: 'taxonomy_id2_cat2',
                type: 'taxonomy'
            },
            {
                name: 'taxonomy_id2_cat2',
                type: 'taxonomy'
            },
            {
                name: 'text_name',
                type: 'text'
            }
        ],
        id: 'Category_2_id',
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
        name: 'Category_3',
        parent: 'Parent',
        metadata: {
            color: '#4200ff'
        },
        type: 'document',
        data_attributes: [
            {
                name: 'taxonomy_id1_cat3',
                type: 'taxonomy'
            },
            {
                name: 'taxonomy_id2_cat3',
                type: 'taxonomy'
            },
            {
                name: 'taxonomy_id3_cat3',
                type: 'taxonomy'
            }
        ],
        id: 'Category_3_id',
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
                name: 'Taxonomy',
                type: 'taxonomy'
            }
        ],
        id: 'Parent',
        parents: [],
        isLeaf: false
    },
    {
        name: 'doc_link1',
        parent: null,
        metadata: {
            color: '#ff0000'
        },
        type: 'document_link',
        data_attributes: [],
        id: 'doc_link1',
        parents: [],
        isLeaf: true
    },
    {
        name: 'doc_link2',
        parent: null,
        metadata: {
            color: '#000000'
        },
        type: 'document_link',
        data_attributes: [],
        id: 'doc_link2',
        parents: [],
        isLeaf: true
    },
    {
        name: 'doc1',
        parent: null,
        metadata: {
            color: '#000000'
        },
        type: 'document',
        data_attributes: [],
        id: 'doc1',
        parents: [],
        isLeaf: true
    },
    {
        name: 'doc2',
        parent: null,
        metadata: {
            color: '#000000'
        },
        type: 'document',
        data_attributes: [],
        id: 'doc2',
        parents: [],
        isLeaf: true
    },
    {
        name: 'link',
        parent: null,
        metadata: {
            color: '#000000'
        },
        type: 'link',
        data_attributes: [],
        id: 'link',
        parents: [],
        isLeaf: true
    }
];
