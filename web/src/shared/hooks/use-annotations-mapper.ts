// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps, eqeqeq */
import { DependencyList, useCallback, useMemo } from 'react';
import {
    Category,
    CategoryDataAttributeWithLabel,
    CategoryDataAttributeWithValue,
    PageInfo,
    Taxon
} from 'api/typings';
import { mapAnnotationFromApi } from 'connectors/task-annotator-connector/task-annotator-utils';
import { Annotation, AnnotationLabel, PageToken } from 'shared';
import { sortByCoordinates } from '../../components/task/task-sidebar-flow/utils';

interface AnnotationsMapperValue {
    getAnnotationLabels: (
        pageKey: string,
        annotation: Annotation,
        category?: Category
    ) => AnnotationLabel[];
    mapAnnotationPagesFromApi: <PageType extends PageInfo>(
        getPageKey: (page: PageType) => string,
        annotationsPages: PageType[],
        categories?: Category[]
    ) => Record<string, Annotation[]>;
}

const getTopRightToken = (tokens?: PageToken[]) => {
    let topRightToken: PageToken | null = null;
    if (!tokens) return;
    for (const token of tokens) {
        if (
            !topRightToken ||
            (token.x + token.width >= topRightToken.x + topRightToken.width &&
                token.y <= topRightToken.y)
        ) {
            topRightToken = token;
        }
    }
    return topRightToken;
};

const getTokenKey = (pageKey: string, token: PageToken) =>
    `${pageKey}_${token.text}_${token.x}_${token.y}`;

export default function useAnnotationsMapper(
    taxonLabels: Map<string, Taxon>,
    deps: DependencyList
): AnnotationsMapperValue {
    const tokenLabelsMap = useMemo(() => new Map<string, AnnotationLabel[]>(), deps);

    const getAnnotationLabels = useCallback(
        (pageKey: string, annotation: Annotation, category?: Category): AnnotationLabel[] => {
            if (annotation.boundType !== 'text') {
                return [];
            }
            const dataAttr: CategoryDataAttributeWithLabel = annotation.data?.dataAttributes
                ? annotation.data?.dataAttributes.find(
                      (attr: CategoryDataAttributeWithValue) => attr.type === 'taxonomy'
                  )
                : null;

            const label = {
                annotationId: annotation.id,
                label: dataAttr && dataAttr.value ? annotation.label : category?.name,
                color: category?.metadata?.color
            };
            const topRightToken: PageToken | null | undefined = getTopRightToken(
                annotation?.tokens
            );
            if (!topRightToken) {
                return [label];
            }
            const tokenKey: string = getTokenKey(pageKey, topRightToken);
            const labels: AnnotationLabel[] = tokenLabelsMap.get(tokenKey) ?? [];
            labels.push(label);
            tokenLabelsMap.set(tokenKey, labels);

            return labels;
        },
        [tokenLabelsMap]
    );

    const mapAnnotationPagesFromApi = useCallback(
        <PageType extends PageInfo>(
            getPageKey: (page: PageType) => string,
            annotationsPages: PageType[],
            categories?: Category[]
        ): Record<string, Annotation[]> => {
            const result: Record<string, Annotation[]> = {};
            annotationsPages.forEach((page) => {
                const pageKey = getPageKey(page);
                const pageAnnotations = page.objs.map((obj) => {
                    const category = categories?.find((category) => category.id == obj.category);
                    const annotation = mapAnnotationFromApi(
                        obj,
                        page.page_num,
                        category,
                        taxonLabels
                    );
                    return {
                        ...annotation,
                        categoryName: category?.name,
                        labels: getAnnotationLabels(pageKey, annotation, category),
                        pageNum: page.page_num
                    };
                });

                /* Merge cells into tables */
                for (let annotation of pageAnnotations) {
                    if (annotation.boundType !== 'table') continue;
                    const relatedCells = pageAnnotations.filter(
                        (el) =>
                            (annotation.children as number[])?.includes(el.id as number) &&
                            el.boundType === 'table_cell'
                    );
                    annotation.tableCells = relatedCells;
                }

                const filteredAnnotations = pageAnnotations
                    .filter((el) => el.boundType !== 'table_cell')
                    .sort(sortByCoordinates);
                result[pageKey] = [...(result[pageKey] ?? []), ...filteredAnnotations];
            });

            return result;
        },
        [getAnnotationLabels]
    );

    return useMemo(
        () => ({
            getAnnotationLabels,
            mapAnnotationPagesFromApi
        }),
        [getAnnotationLabels, mapAnnotationPagesFromApi]
    );
}
