import { Category, CategoryDataAttributeWithValue, PageInfo } from 'api/typings';
import { mapAnnotationFromApi } from 'connectors/task-annotator-connector/task-annotator-utils';
import { DependencyList, useCallback, useMemo } from 'react';
import { Annotation, AnnotationLabel, PageToken } from 'shared';

interface AnnotationsMapperValue {
    getAnnotationLabels: (
        pageKey: string,
        ann: Annotation,
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

export default function useAnnotationsMapper(deps: DependencyList): AnnotationsMapperValue {
    const tokenLabelsMap = useMemo(() => new Map<string, AnnotationLabel[]>(), deps);

    const getAnnotationLabels = useCallback(
        (pageKey: string, ann: Annotation, category?: Category): AnnotationLabel[] => {
            if (ann.boundType !== 'text') {
                return [];
            }
            const dataAttr: CategoryDataAttributeWithValue = ann.data?.dataAttributes
                ? ann.data?.dataAttributes.find(
                      (attr: CategoryDataAttributeWithValue) => attr.type === 'taxonomy'
                  )
                : null;
            const label = {
                annotationId: ann.id,
                label: dataAttr ? dataAttr.value : category?.name,
                color: category?.metadata?.color
            };
            const topRightToken: PageToken | null | undefined = getTopRightToken(ann?.tokens);
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
                    const ann = mapAnnotationFromApi(obj, category);
                    return {
                        ...ann,
                        labels: getAnnotationLabels(pageKey, ann, category)
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
