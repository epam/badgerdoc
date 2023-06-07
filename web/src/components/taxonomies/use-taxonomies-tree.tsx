import { taxonsFetcher } from 'api/hooks/taxons';
import {
    Operators,
    SortingDirection,
    FilterWithDocumentExtraOption,
    TaxonomyNode,
    Taxon
} from 'api/typings';
import { useState, useEffect, useCallback, useRef } from 'react';
import { updateTreeData } from 'shared/components/badger-tree/update-tree-data';
import { mapTaxons, mapTaxon } from './map-taxonomies';

interface Props {
    searchText: string;
    taxonomyId?: string;
    taxonomyFilter?: FilterWithDocumentExtraOption<keyof Taxon>;
}

export const useTaxonomiesTree = ({ searchText, taxonomyId, taxonomyFilter }: Props) => {
    const [taxonomyNodes, setTaxonomyNodes] = useState<TaxonomyNode[]>([]);
    const [expandNode, setExpandNode] = useState<string>();
    const [isLoading, setIsLoading] = useState(false);

    const branchesInProgress = useRef(new Set());
    const abortController = useRef<AbortController>();

    const handleSetTaxonsNodes = (data: Taxon[], parentKey?: string) => {
        if (!data) return;

        if (parentKey) {
            setExpandNode(undefined);
            const childNodes = data.map((taxon) => mapTaxon(taxon));
            setTaxonomyNodes((prevState) => updateTreeData(prevState, parentKey, childNodes));
        } else {
            setTaxonomyNodes((prevState) => {
                const updatedNodes = prevState.map((prevNode) => {
                    const matchingNode = mapTaxons(data).find(
                        (newNode) => newNode.key === prevNode.key
                    );
                    if (matchingNode) {
                        const childrens = [...prevNode.children, ...matchingNode.children];
                        const set = new Set();
                        const combinedChildren = childrens.filter(({ key }) => {
                            return !set.has(key) && set.add(key);
                        });

                        return { ...prevNode, children: combinedChildren };
                    }
                    return prevNode;
                });

                const newNodes = mapTaxons(data).filter((newNode) =>
                    prevState.every((prevNode) => prevNode.key !== newNode.key)
                );

                return [...updatedNodes, ...newNodes];
            });
        }
    };

    const handleLoadFullList = async ({
        filters,
        parentId,
        search
    }: {
        filters: FilterWithDocumentExtraOption<keyof Taxon>[];
        parentId?: string;
        search?: string;
    }) => {
        let page = 1;
        const size = 100;
        let isEmpty = false;
        const currentBranchName = parentId ?? 'root';
        branchesInProgress.current.add(currentBranchName);

        setIsLoading(true);

        do {
            abortController.current = new AbortController();

            const { data } = await taxonsFetcher({
                page,
                size,
                filters,
                searchText: search,
                signal: abortController.current.signal,
                sortConfig: { field: 'name', direction: SortingDirection.ASC }
            });

            handleSetTaxonsNodes(data, parentId);

            if (page > 1 || !data.length) {
                setIsLoading(false);
            }

            page += 1;
            isEmpty = !data.length;
        } while (!isEmpty && branchesInProgress.current.has(currentBranchName));

        abortController.current = undefined;
    };

    const handleLoadData = useCallback(
        async (search?: string) => {
            if (!taxonomyId) return;
            handleLoadFullList({
                search,
                filters: [
                    taxonomyFilter ?? {
                        field: 'taxonomy_id',
                        operator: Operators.EQ,
                        value: taxonomyId ?? []
                    }
                ]
            });
        },
        [taxonomyFilter, taxonomyId]
    );

    const handleLoadMore = useCallback(async (node: TaxonomyNode) => {
        setExpandNode(node.key);
        handleLoadFullList({
            filters: [
                {
                    field: 'parent_id',
                    operator: Operators.EQ,
                    value: node.key
                }
            ],
            parentId: node.key
        });
    }, []);

    useEffect(() => {
        setTaxonomyNodes([]);
        branchesInProgress.current.clear();
        abortController.current?.abort();

        handleLoadData(searchText);
    }, [handleLoadData, searchText]);

    return {
        taxonomyNodes,
        expandNode,
        onLoadData: handleLoadMore,
        isLoading
    };
};
