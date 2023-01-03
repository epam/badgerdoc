import { Taxon } from 'api/typings';

export const taxons: Taxon[] = [
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
    },
    {
        name: 'Parent1',
        parent_id: null,
        id: 'Parent1',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent2',
        parent_id: null,
        id: 'Parent2',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent3',
        parent_id: null,
        id: 'Parent3',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent4',
        parent_id: null,
        id: 'Parent4',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent5',
        parent_id: null,
        id: 'Parent5',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent6',
        parent_id: null,
        id: 'Parent6',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent7',
        parent_id: null,
        id: 'Parent7',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent8',
        parent_id: null,
        id: 'Parent8',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent9',
        parent_id: null,
        id: 'Parent9',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent10',
        parent_id: null,
        id: 'Parent10',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent11',
        parent_id: null,
        id: 'Parent11',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent12',
        parent_id: null,
        id: 'Parent12',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent13',
        parent_id: null,
        id: 'Parent13',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent14',
        parent_id: null,
        id: 'Parent14',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent15',
        parent_id: null,
        id: 'Parent15',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent16',
        parent_id: null,
        id: 'Parent16',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent17',
        parent_id: null,
        id: 'Parent17',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent18',
        parent_id: null,
        id: 'Parent18',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent19',
        parent_id: null,
        id: 'Parent19',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent20',
        parent_id: null,
        id: 'Parent20',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent21',
        parent_id: null,
        id: 'Parent21',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent22',
        parent_id: null,
        id: 'Parent22',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent23',
        parent_id: null,
        id: 'Parent23',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent24',
        parent_id: null,
        id: 'Parent24',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent25',
        parent_id: null,
        id: 'Parent25',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent26',
        parent_id: null,
        id: 'Parent26',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent27',
        parent_id: null,
        id: 'Parent27',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent28',
        parent_id: null,
        id: 'Parent28',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    },
    {
        name: 'Parent29',
        parent_id: null,
        id: 'Parent29',
        parents: [],
        is_leaf: false,
        taxonomy_id: 'Taxonomy'
    }
];
