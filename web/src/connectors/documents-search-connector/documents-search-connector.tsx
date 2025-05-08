// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import React, { FC, useEffect, useState, useContext } from 'react';
import styles from './documents-search-connector.module.scss';
import { Checkbox, SearchInput, LinkButton } from '@epam/loveship';
import { FacetName, Facets, FacetValue } from 'api/typings/search';
import { useFacets } from 'api/hooks/search';
import { DocumentsSearch } from 'shared/contexts/documents-search';

// Define FacetValuesFilter locally to match DocumentsSearchProvider
type FacetValuesFilter = Array<{ id: string; value: boolean }>;

type SearchFacet = {
    category: string;
    job_id: string;
};

type FacetFilter = {
    category: Array<{ id: string; value: boolean }>;
    job_id: Array<{ id: string; value: boolean }>;
};

const mapFacetName = (name: FacetName): string => {
    switch (name) {
        case 'category':
            return 'Categories';
        case 'job_id':
            return 'Extractions';
        default:
            return name;
    }
};

export const DocumentsSearchConnector: FC = () => {
    const { facetFilter, onFacetFilterChange, onValueChange } = useContext(DocumentsSearch);

    const [facetState, setFacetState] = useState<Facets[]>([]);
    const [search, setSearch] = useState<SearchFacet>({
        category: '',
        job_id: ''
    });
    const [limit, setLimit] = useState({
        category: 6,
        job_id: 6
    });

    const findFilters = (name: FacetName): string[] => {
        return facetFilter[name].filter((filter) => filter.value).map(({ id }) => id);
    };

    const { data } = useFacets({
        query: '',
        categoryLimit: limit.category,
        jobLimit: limit.job_id,
        categoryFilter: findFilters('category'),
        jobFilter: findFilters('job_id')
    });

    const mapFilters = (facets: Facets[]) => {
        facets.forEach(({ name, values }) => {
            const facetValues: FacetValuesFilter = values.map(({ id }) => ({
                id: id.toString(),
                value:
                    facetFilter[name].find((filter) => filter.id === id.toString())?.value ?? false
            }));
            onFacetFilterChange(name, facetValues);
        });
    };

    const findFacet = (
        facetName: FacetName,
        facetData: Facets[] = facetState
    ): Facets | undefined => {
        return facetData.find(({ name }) => name === facetName);
    };

    const isShowButton = (facetName: FacetName, facetData: Facets[] = facetState): boolean => {
        return (findFacet(facetName, facetData)?.values.length ?? 0) >= 6;
    };

    const [isShowMore, setIsShowMore] = useState({
        category: false,
        job_id: false
    });

    const filterValue = (facetName: FacetName, searchText: string) => {
        if (data) {
            const findedFacet = findFacet(facetName, data.facets);
            const filteredValue = findedFacet?.values.filter(
                ({ id }) => id.toLowerCase().indexOf(searchText.toLowerCase()) >= 0
            );
            const indexFacet = data.facets.findIndex(({ name }) => name === facetName);
            const copyFacets = JSON.parse(JSON.stringify(data.facets));

            if (filteredValue) {
                copyFacets[indexFacet].values = filteredValue;
                setFacetState(copyFacets);
            }
        }
    };

    const isCutValue = (facetName: FacetName, values: FacetValue[]): FacetValue[] => {
        const copyValue = [...values];
        return isShowMore[facetName] ? copyValue.slice(0, 5) : copyValue;
    };

    const onLimitChange = (name: FacetName) => {
        setLimit((prevState) => ({
            ...prevState,
            [name]: 0
        }));
        setIsShowMore((prevState) => ({
            ...prevState,
            [name]: false
        }));
    };

    useEffect(() => {
        if (data) {
            setFacetState(data.facets);
            setIsShowMore({
                category: isShowButton('category', data.facets),
                job_id: isShowButton('job_id', data.facets)
            });
            mapFilters(data.facets);
        }
    }, [data]);

    if (data && facetState.length) {
        return (
            <div className={styles.sidebar}>
                <h2 className={styles['sidebar-title']}>Search options</h2>
                <div className={styles['filter-container']}>
                    {facetState.map(({ name, values }) => (
                        <div key={name} className={styles['facet']}>
                            <h3 className={styles['facet-name']}>{mapFacetName(name)}</h3>
                            <div className={styles['search']}>
                                <SearchInput
                                    value={search[name]}
                                    size="24"
                                    onValueChange={(value) => {
                                        const val = value || '';
                                        setSearch((prev) => ({
                                            ...prev,
                                            [name]: val
                                        }));
                                        filterValue(name, val);
                                    }}
                                    onClick={() => onLimitChange(name)}
                                    placeholder="Search"
                                    debounceDelay={0}
                                />
                            </div>
                            {isCutValue(name, values).map((facet) => (
                                <div key={facet.id} className={styles['facet-item']}>
                                    <Checkbox
                                        value={
                                            facetFilter[name].find(
                                                (filter) => filter.id === facet.id
                                            )?.value ?? false
                                        }
                                        onValueChange={() => onValueChange(name, facet.id)}
                                    />
                                    <span className={styles['facet-id']}>
                                        {`${facet.name} (${facet.count})`}
                                    </span>
                                </div>
                            ))}
                            {isShowMore[name] && (
                                <div className={styles['show-more']}>
                                    <LinkButton
                                        caption="Show more"
                                        onClick={() => onLimitChange(name)}
                                    />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return <div />;
};
