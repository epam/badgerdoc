import { useTaxons } from 'api/hooks/taxons';
import { Operators, PageInfo, SortingDirection, Taxon } from 'api/typings';
import { useEffect, useMemo, useState } from 'react';
import { getTaxonFullName } from 'shared/helpers/get-taxon-full-name';

export default function useAnnotationsTaxons(annotationsByPages?: PageInfo[]): Map<string, Taxon> {
    const [taxonLabels, setTaxonLabels] = useState(new Map<string, Taxon>());

    const taxonIds = useMemo(() => {
        let result: string[] = [];

        if (!annotationsByPages) return result;

        for (let page of annotationsByPages) {
            for (let obj of page.objs) {
                if (
                    obj.data.dataAttributes?.[0] &&
                    obj.data.dataAttributes?.[0].value &&
                    obj.data.dataAttributes?.[0].type === 'taxonomy'
                ) {
                    result.push(obj.data.dataAttributes[0].value);
                }
            }
        }

        return result;
    }, [annotationsByPages]);

    const { data: taxons } = useTaxons(
        {
            page: 1,
            size: 100,
            searchText: '',
            filters: [
                {
                    field: 'id',
                    value: taxonIds,
                    operator: Operators.IN
                }
            ],
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        { enabled: Boolean(taxonIds.length) }
    );

    useEffect(() => {
        if (!taxons?.data) return;

        setTaxonLabels((origin) => {
            return taxons.data.reduce((updatedTaxonLabels, taxon) => {
                updatedTaxonLabels.set(taxon.id, { ...taxon, name: getTaxonFullName(taxon) });
                return updatedTaxonLabels;
            }, new Map(origin));
        });
    }, [taxons]);

    return taxonLabels;
}
