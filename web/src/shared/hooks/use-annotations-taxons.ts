import { useTaxonomies } from 'api/hooks/taxonomies';
import { Operators, PageInfo, SortingDirection, Taxon } from 'api/typings';
import { useEffect, useMemo, useState } from 'react';

export default function useAnnotationsTaxons(annotationsByPages?: PageInfo[]): Map<string, Taxon> {
    const [taxonLabels, setTaxonLabels] = useState(new Map<string, Taxon>());

    let taxonIds: string[] | undefined = useMemo(() => {
        let taxonIdArr: string[] = [];
        if (annotationsByPages) {
            for (let page of annotationsByPages) {
                for (let obj of page.objs) {
                    if (
                        obj.data.dataAttributes[0] &&
                        obj.data.dataAttributes[0].value &&
                        obj.data.dataAttributes[0].type === 'taxonomy'
                    ) {
                        taxonIdArr.push(obj.data.dataAttributes[0].value);
                    }
                }
            }
            return taxonIdArr;
        }
    }, [annotationsByPages]);

    const { data: taxons, refetch } = useTaxonomies(
        {
            page: 1,
            size: 100,
            searchText: '',
            filters: [
                {
                    field: 'id',
                    operator: Operators.IN,
                    value: taxonIds
                }
            ],
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        { enabled: false }
    );

    useEffect(() => {
        if (taxonIds) {
            refetch();
        }
    }, [taxonIds]);

    useEffect(() => {
        if (taxons?.data) {
            setTaxonLabels(new Map(taxons.data.map((taxon) => [taxon.id, taxon])));
        }
    }, [taxons?.data]);

    return taxonLabels;
}
