import { DependencyList, useCallback, useMemo } from 'react';
import { Category, CategoryDataAttributeWithValue, PageInfo, Taxon } from 'api/typings';
import { mapAnnotationFromApi } from 'connectors/task-annotator-connector/task-annotator-utils';
import { Annotation, AnnotationLabel, PageToken } from 'shared';

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

export default function useAnnotationsMapper(
    taxonLabels: Map<string, Taxon>,
    deps: DependencyList
): AnnotationsMapperValue {
    const tokenLabelsMap = useMemo(() => new Map<string, AnnotationLabel[]>(), deps);

    const getAnnotationLabels = useCallback(
        (pageKey: string, annotation: Annotation, category?: Category) => {
            if (annotation.boundType !== 'text') {
                return [];
            }

            const isTaxonomyExisted = annotation.data?.dataAttributes?.find(
                ({ type }: CategoryDataAttributeWithValue) => type === 'taxonomy'
            )?.value;

            const label = {
                annotationId: annotation.id,
                color: category?.metadata?.color,
                label: isTaxonomyExisted ? annotation.label : category?.name
            };
            const topRightToken = getTopRightToken(annotation?.tokens);

            if (!topRightToken) {
                return [label];
            }

            const tokenKey = `${pageKey}_${topRightToken.text}_${topRightToken.x}_${topRightToken.y}`;
            const labels = tokenLabelsMap.get(tokenKey) ?? [];
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
                    const annotation = mapAnnotationFromApi(obj, category, taxonLabels);
                    return {
                        ...annotation,
                        categoryName: category?.name,
                        labels: getAnnotationLabels(pageKey, annotation, category)
                    };
                });
                /* Merge cells into tables */
                for (let annotation of pageAnnotations) {
                    if (annotation.boundType !== 'table') continue;
                    const relatedCells = pageAnnotations.filter(
                        (el) =>
                            annotation.children?.includes(el.id) && el.boundType === 'table_cell'
                    );
                    annotation.tableCells = relatedCells;
                }
                const filteredAnnotations = pageAnnotations.filter(
                    (el) => el.boundType !== 'table_cell'
                );
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
