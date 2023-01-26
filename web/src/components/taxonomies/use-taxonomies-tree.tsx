import { taxonsFetcher, useTaxons } from 'api/hooks/taxons';
import { Operators, SortingDirection, Filter, TaxonomyNode, Taxon } from 'api/typings';
import { isEmpty } from 'lodash';
import { useState, useEffect } from 'react';
import { updateTreeData } from 'shared/components/badger-tree/update-tree-data';
import { mapTaxons, mapTaxon } from './map-taxonomies';

interface Props {
    searchText: string;
    taxonomyId?: string;
    taxonomyFilter?: Filter<keyof Taxon>;
}

export const useTaxonomiesTree = ({ searchText, taxonomyId, taxonomyFilter }: Props) => {
    const [taxonomyNodes, setTaxonomyNodes] = useState<TaxonomyNode[]>([]);
    const [expandNode, setExpandNode] = useState<string>();

    if (!taxonomyFilter) {
        taxonomyFilter = {
            field: 'taxonomy_id',
            operator: Operators.EQ,
            value: taxonomyId ?? []
        };
    }

    const { data: rootCategories, isFetched } = useTaxons(
        {
            page: 1,
            size: 100,
            searchText: '',
            filters: [
                {
                    field: 'parent_id',
                    operator: Operators.IS_NULL
                },
                taxonomyFilter
            ],
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        {}
    );
    const searchResult = useTaxons(
        {
            page: 1,
            size: 100,
            searchText,
            filters: [taxonomyFilter],
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        { enabled: false, cacheTime: 0 }
    );
    useEffect(() => {
        if (searchText) {
            searchResult.refetch();
        }
    }, [searchText]);

    useEffect(() => {
        if (searchText) {
            if (searchResult.data?.data) {
                setTaxonomyNodes(mapTaxons(searchResult.data?.data));
            } else {
                setTaxonomyNodes([]);
            }
        } else {
            setTaxonomyNodes(mapTaxons(rootCategories?.data));
        }
    }, [rootCategories, searchResult.data, searchText]);

    const onLoadData = async (node: TaxonomyNode) => {
        if (!isEmpty(node.children)) {
            return node.children;
        }
        setExpandNode(node.key);
        const parentFilter: Filter<keyof Taxon> = {
            field: 'parent_id',
            operator: Operators.EQ,
            value: node.key
        };
        const childTaxons = await taxonsFetcher(1, 100, '', [parentFilter]);

        if (childTaxons) {
            setExpandNode(undefined);
            const childNodes = childTaxons.data.map((taxon) => mapTaxon(taxon));
            setTaxonomyNodes((prevState) => updateTreeData(prevState, node.key, childNodes));
        }
        return node.children;
    };
    return { taxonomyNodes, expandNode, onLoadData, searchResult, rootCategories, isFetched };
};
