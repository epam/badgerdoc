import { useTaxons } from 'api/hooks/taxons';
import { Operators, PageInfo, SortingDirection, Taxon } from 'api/typings';
import { useEffect, useMemo, useState } from 'react';

export default function useAnnotationsTaxons(annotationsByPages?: PageInfo[]): Map<string, Taxon> {
    const [taxonLabels, setTaxonLabels] = useState(new Map<string, Taxon>());
    const updateMap = (key: string, value: Taxon) => {
        setTaxonLabels(new Map(taxonLabels.set(key, value)));
    };

    let taxonIds: string[] | undefined = useMemo(() => {
        let taxonIdArr: string[] = [];
        if (annotationsByPages) {
            for (let page of annotationsByPages) {
                for (let obj of page.objs) {
                    if (
                        obj.data.dataAttributes?.[0] &&
                        obj.data.dataAttributes?.[0].value &&
                        obj.data.dataAttributes?.[0].type === 'taxonomy'
                    ) {
                        taxonIdArr.push(obj.data.dataAttributes[0].value);
                    }
                }
            }
            return taxonIdArr;
        }
    }, [annotationsByPages]);

    const { data: taxons, refetch } = useTaxons(
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
        if (taxonIds && taxonIds.length) {
            refetch();
        }
    }, [taxonIds]);

    useEffect(() => {
        if (taxons?.data) {
            taxons.data.forEach((taxon: Taxon) => {
                updateMap(taxon.id, taxon);
            });
        }
    }, [taxons?.data]);

    return taxonLabels;
}
