// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import React, { FC, useEffect, useState, useContext } from 'react';
import styles from './documents-search-connector.module.scss';
import { Checkbox, SearchInput, LinkButton } from '@epam/loveship';
import { FacetName, Facets, FacetValue, FacetValuesFilter } from 'api/typings/search';
import { useFacets } from 'api/hooks/search';
import { DocumentsSearch } from 'shared/contexts/documents-search';

type SearchFacet = {
    category: string;
    job_id: string;
};

const mapFacetName = (name: FacetName) => {
    switch (name) {
        case 'category':
            return 'Categories';
        case 'job_id':
            return 'Extractions';
    }
};

export const DocumentsSearchConnector: FC = () => {
    const { facetFilter, setFacetFilter } = useContext(DocumentsSearch);

    const [facetState, setFacetState] = useState<Facets[]>([]);
    const [search, setSearch] = useState<SearchFacet>({
        category: '',
        job_id: ''
    });
    const [limit, setLimit] = useState({
        category: 6,
        job_id: 6
    });

    const findFilters = (name: FacetName) => {
        const mapFilters = Object.values(facetFilter[name]).map((filter) => filter);
        const findFilters = mapFilters.filter((el) => el.value === true);
        return findFilters.map(({ id }) => id);
    };

    const { data } = useFacets({
        query: '',
        categoryLimit: limit.category,
        jobLimit: limit.job_id,
        categoryFilter: findFilters('category'),
        jobFilter: findFilters('job_id')
    });

    const onFacetFilterChange = (name: FacetName, filterValue: FacetValuesFilter[]) => {
        setFacetFilter((prevState: any) => {
            const copyFilters = Object.assign({}, prevState);
            copyFilters[name] = filterValue;
            return copyFilters;
        });
    };

    const mapFilters = (facets: Facets[]) => {
        facets.forEach(({ name, values }) => {
            const facetValues: any = {};
            values.forEach(({ id }) => {
                facetValues[id] = {
                    id: id.toString(),
                    // @ts-ignore: Unreachable code error
                    value: facetFilter[name][id.toString()]?.value ?? false
                };
            });

            onFacetFilterChange(name, facetValues);
        });
    };

    const onValueChange = (name: FacetName, id: string) => {
        setFacetFilter((prevState: any) => {
            const copyFilters = Object.assign({}, prevState);
            // @ts-ignore: Unreachable code error
            copyFilters[name][id].value = !copyFilters[name][id].value;
            return copyFilters;
        });
    };

    const findFacet = (facetName: FacetName, facetData: Facets[] = facetState) => {
        return facetData.find(({ name }) => name === facetName);
    };

    const isShowButton = (facetName: FacetName, facetData: Facets[] = facetState) => {
        return findFacet(facetName, facetData)?.values.length === 6;
    };

    const [isShowMore, setIsShowMore] = useState({
        category: false,
        job_id: false
    });

    const filterValue = (facetName: FacetName, searchText: string) => {
        if (data) {
            const findedFacet = findFacet(facetName, data.facets);
            const filteredValue = findedFacet?.values.filter(
                ({ id }) => id.indexOf(searchText, 0) >= 0
            );
            const indexFacet = data.facets.findIndex(({ name }) => name === facetName);
            const copyFacets = JSON.parse(JSON.stringify(data.facets));

            if (filteredValue) {
                copyFacets[indexFacet].values = filteredValue;
                setFacetState(copyFacets);
            }
        }
    };

    const isCutValue = (facetName: FacetName, values: FacetValue[]) => {
        const copyValue = [...values];
        return isShowMore[facetName] ? copyValue.splice(0, 5) : copyValue;
    };

    const onLimitChange = (name: FacetName) => {
        setLimit((prevState) => {
            const copyLimit = Object.assign({}, prevState);
            copyLimit[name] = 0;
            return copyLimit;
        });
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
                                        const copySearch = Object.assign({}, search);
                                        copySearch[name] = val;
                                        setSearch(copySearch);
                                        filterValue('category', val);
                                    }}
                                    onClick={() => onLimitChange(name)}
                                    placeholder="Search"
                                    debounceDelay={0}
                                />
                            </div>
                            {isCutValue(name, values).map((facet) => (
                                <div key={facet.id} className={styles['facet-item']}>
                                    <Checkbox
                                        // @ts-ignore: Unreachable code error
                                        value={facetFilter[name][facet.id].value}
                                        onValueChange={() => onValueChange(name, facet.id)}
                                    />
                                    <span key={facet.id} className={styles['facet-id']}>
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
