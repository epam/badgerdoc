import { Taxon, TaxonomyNode } from 'api/typings';
import { getTaxonFullName } from 'shared/helpers/get-taxon-full-name';

export const mapTaxon = (taxon: Taxon): TaxonomyNode => ({
    key: taxon.id,
    title: taxon.name,
    isLeaf: taxon.is_leaf,
    children: [],
    taxon: { ...taxon, name: getTaxonFullName(taxon) }
});

export const mapTaxons = (taxonomies?: Taxon[]): TaxonomyNode[] => {
    if (!taxonomies) {
        return [];
    }
    const nodeById = new Map<string, TaxonomyNode>();
    const rootNodes = [];

    const setNode = (taxonomy: Taxon) => {
        const taxonomyNode = mapTaxon(taxonomy);
        if (!nodeById.has(taxonomy.id)) {
            nodeById.set(taxonomy.id, taxonomyNode);
        }
    };

    for (const taxonomy of taxonomies) {
        setNode(taxonomy);
        if (taxonomy.parents?.length) {
            for (let parentCategory of taxonomy.parents) {
                setNode(parentCategory);
            }
        }
    }

    for (let [, value] of nodeById) {
        if (!value.taxon?.parent_id) {
            rootNodes.push(value);
        } else {
            const parent = nodeById.get(value.taxon.parent_id);
            if (parent) {
                parent.children.push(value);
            }
        }
    }

    return rootNodes;
};
