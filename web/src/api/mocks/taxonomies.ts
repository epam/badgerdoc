import { Taxon } from 'api/typings';

export const taxonomies: Taxon[] = [
    {
        name: 'Child1',
        parent_id: 'Parent',
        id: 'Child1',
        parents: [
            {
                name: 'Parent',
                parent_id: null,
                id: 'Parent',
                is_leaf: false,
                taxonomy_id: 'Taxonomy'
            }
        ],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Child1.1',
        parent_id: 'Child1',
        id: 'Child1.1',
        parents: [
            {
                name: 'Child1',
                parent_id: 'Parent',
                taxonomy_id: 'Taxonomy',
                id: 'Child1',
                is_leaf: false
            },
            {
                name: 'Parent',
                parent_id: null,
                id: 'Parent',
                is_leaf: false,
                taxonomy_id: 'Taxonomy'
            }
        ],
        is_leaf: true,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Child2',
        parent_id: 'Parent',
        id: 'Child2',
        parents: [
            {
                name: 'Parent',
                parent_id: null,
                id: 'Parent',
                is_leaf: false,
                taxonomy_id: 'Taxonomy'
            }
        ],
        is_leaf: true,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent',
        parent_id: null,
        id: 'Parent',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    }
];
