import {
    CategoryDataAttribute,
    CategoryDataAttributeWithValue,
    PageInfoObjs,
    PageInfo,
    Category,
    CategoryDataAttrType,
    ExternalViewerState
} from 'api/typings';

import {
    Annotation,
    AnnotationBoundType,
    AnnotationLabel,
    AnnotationTable,
    PageToken,
    TableApi
} from 'shared';
import { isIntersected, isR2InsideR1 } from 'shared/components/annotator/utils/is-intersected';
import { annotationToRect, tokenToRect } from 'shared/components/annotator/utils/to-rect-utils';
import { bboxToBound } from 'shared/helpers/bbox-to-bound';
import { boundToBBox } from 'shared/helpers/bound-to-bbox';
import { boundToRect } from '../../shared/components/annotator/utils/rect-to-bound';

const categoryDataAttrsCache = new Map();
export const defaultExternalViewer: ExternalViewerState = {
    isOpen: false,
    type: '',
    name: '',
    value: ''
};

/**
 * Category types for external viewer
 */
export const molecule: CategoryDataAttrType = 'molecule';
export const latex: CategoryDataAttrType = 'latex';

export const isValidCategoryType = (type: CategoryDataAttrType) => {
    if (type === molecule || type === latex) {
        return true;
    }
    return false;
};

export const getCategoryDataAttrs = (
    annotationLabel: string | number | undefined,
    categories: Category[] | undefined
) => {
    /**
     * @param annotationLabel - The annotation label (name category too)
     * @param categories - The array of categories
     * @returns The data attribute(s) of category.
     *
     * The function checks if the hash contains an array of data attributes.
     * If not, it finds the value and stores it in the hash.
     */

    if (!categoryDataAttrsCache.has(annotationLabel)) {
        const foundCategoryDataAttrs = categories?.find(
            (el) => el.name.toString() === annotationLabel
        )?.data_attributes;
        categoryDataAttrsCache.set(annotationLabel, foundCategoryDataAttrs);
    }

    return categoryDataAttrsCache.get(annotationLabel);
};

export const mapAnnDataAttrs = (
    foundCategoryDataAttrs: Array<CategoryDataAttribute>,
    dataAttrItem: Array<CategoryDataAttributeWithValue> | undefined
) => {
    return foundCategoryDataAttrs.map((dataAtt: { name: string; type: CategoryDataAttrType }) => {
        const attrsValue =
            (dataAttrItem && dataAttrItem.find((el) => el.name === dataAtt.name)?.value) || '';

        return {
            name: dataAtt.name,
            type: dataAtt.type,
            value: attrsValue
        };
    });
};

const addTableValues = (ann: Annotation): TableApi => {
    const cols: number[] = [];
    const rows: number[] = [];
    cols.push(ann.bound.x);
    rows.push(ann.bound.y);
    for (let col of ann.table!.cols) {
        cols.push(ann.bound.x + col);
    }
    for (let row of ann.table!.rows) {
        rows.push(ann.bound.y + row);
    }

    cols.push(ann.bound.x + ann.bound.width);
    rows.push(ann.bound.y + ann.bound.height);
    return {
        cols,
        rows
    };
};

const mapAnnotationToApi = (
    ann: Annotation,
    annotationDataAttrs: Record<number, Array<CategoryDataAttributeWithValue>>,
    tokens: PageToken[]
): PageInfoObjs[] => {
    const annDataAttrsItem = annotationDataAttrs[+ann.id];
    const filteredDataAttrs = annDataAttrsItem
        ? annDataAttrsItem.filter(({ value }) => value.trim() !== '')
        : [];
    // TODO: if no tokens are available, inform user?
    const tokensByAnnotation = ann.tokens
        ? ann.tokens?.map((token) => token.text).join(' ')
        : (tokens ?? [])
              .filter((token) => isIntersected(tokenToRect(token), annotationToRect(ann)))
              .map((token) => token?.text)
              .join(' ');

    if (ann.boundType === 'table') {
        const cells: PageInfoObjs[] = [...(ann.tableCells as Annotation[])].map((el) => ({
            id: +el.id,
            type: el.boundType,
            bbox: boundToBBox(el.bound),
            category: el.category,
            data: {
                tokens: el.tokens,
                dataAttributes: filteredDataAttrs,
                row: el.data?.row,
                col: el.data?.col,
                rowspan: el.data?.rowspan,
                colspan: el.data?.colspan
            },
            links: el.links
        }));
        return [
            {
                id: +ann.id,
                type: ann.boundType,
                bbox: boundToBBox(ann.bound),
                category: ann.category,
                data: {
                    tokens: ann.tokens,
                    dataAttributes: filteredDataAttrs,
                    table: addTableValues(ann),
                    rowspan: ann.data?.rowspan,
                    colspan: ann.data?.colspan,
                    ...addTableValues(ann)
                },
                children: ann.children,
                links: ann.links
            },
            ...cells
        ];
    }

    return [
        {
            id: +ann.id,
            type: ann.boundType,
            bbox: boundToBBox(ann.bound),
            category: ann.category,
            data: {
                tokens: ann.tokens,
                dataAttributes: filteredDataAttrs,
                table: ann.table,
                rows: ann.table?.rows,
                cols: ann.table?.cols,
                row: ann.data?.row,
                col: ann.data?.col,
                rowspan: ann.data?.rowspan,
                colspan: ann.data?.colspan
            },
            children: ann.children,
            text: tokensByAnnotation,
            links: ann.links,
            segments: ann.segments
        }
    ];
};

const addChildrenToAnnotation = (parent: Annotation, annotations: Annotation[]): Annotation => {
    const children: number[] = (parent.children as number[]) ?? [];
    for (let ann of annotations) {
        if (ann.boundType !== 'text') {
            if (
                isR2InsideR1(boundToRect(parent.bound), boundToRect(ann.bound)) &&
                ann.id !== parent.id &&
                !children.includes(+ann.id)
            ) {
                children.push(+ann.id);
            }
        } else {
            if (ann.tokens) {
                let needToPush: boolean = true;
                for (let token of ann.tokens) {
                    if (!token || !token.id) {
                        needToPush = false;
                        break;
                    }
                    if (
                        !isR2InsideR1(boundToRect(parent.bound), tokenToRect(token)) ||
                        token.id === parent.id ||
                        children.includes(+token.id) ||
                        children.includes(+ann.id)
                    ) {
                        needToPush = false;
                        break;
                    }
                }
                if (needToPush) {
                    children.push(+ann.id);
                }
            }
        }
    }
    return {
        ...parent,
        children
    };
};

export const mapModifiedAnnotationPagesToApi = (
    modifiedPagesNums: number[],
    annotationsByPageNum: Record<number, Annotation[]>,
    tokensByPages: Record<number, PageToken[]>,
    pages: PageInfo[],
    annotationDataAttrs: Record<number, Array<CategoryDataAttributeWithValue>>,
    defaultPageSize: { width: number; height: number }
): PageInfo[] => {
    return modifiedPagesNums.map((page_num) => {
        const annotations = annotationsByPageNum[page_num];
        const tokens = tokensByPages[page_num];
        const pageSize = pages.find((page) => page.page_num === page_num)?.size;
        const annotationWithChildren = annotations.map((el) =>
            addChildrenToAnnotation(el, annotations)
        );
        return {
            page_num,
            size: pageSize ?? defaultPageSize,
            objs: annotationWithChildren
                .map((annotation) => mapAnnotationToApi(annotation, annotationDataAttrs, tokens))
                .flat()
        };
    });
};

const formatTable = (table: TableApi): AnnotationTable => {
    if (!table.cols || !table.rows)
        return {
            cols: [],
            rows: []
        };
    /* For some reason, backend send data in specific format: [tableLeftBorder, firstGutter, secondGutter, ..., lastGutter, tableEndBorder]
     * so we need to remove first and last entries from mentioned array here */
    const newCols: number[] = table.cols.slice(1, -1);
    const newRows: number[] = table.rows.slice(1, -1);
    /* We are also expecting gutter position to be relative to table start, but backend send data relative to page
     * so we need to adjust for that */
    newCols.forEach((o, i, a) => (a[i] -= table.cols[0]));
    newRows.forEach((o, i, a) => (a[i] -= table.rows[0]));
    /* Finally, we're expecting those gutters to be sorted, so we need to enforce that somewhere
     * Please be careful here - if we'll receive NAN, Infinity, etc. - everything will immediately crash */
    return {
        cols: newCols.sort((a, b) => a - b),
        rows: newRows.sort((a, b) => a - b)
    };
};

export const mapAnnotationFromApi = (obj: PageInfoObjs, category?: Category): Annotation => {
    let dataAttr: CategoryDataAttributeWithValue | null = null;
    if (obj.data.dataAttributes) {
        dataAttr = obj.data.dataAttributes.find(
            (attr: CategoryDataAttributeWithValue) => attr.type === 'taxonomy'
        );
    }
    return {
        id: obj.id!,
        boundType: (obj.type as AnnotationBoundType) || 'box',
        bound: bboxToBound(obj.bbox),
        category: obj.category,
        color: category?.metadata?.color,
        label: dataAttr ? dataAttr.value : category?.name,
        tokens: obj.data?.tokens,
        links: obj?.links,
        data: obj.data,
        table: (obj.type as AnnotationBoundType) === 'table' ? formatTable(obj.data) : undefined,
        children: obj.children,
        tableCells: (obj.type as AnnotationBoundType) === 'table' ? [] : undefined,
        segments: obj.segments
    };
};

export const mapAnnotationDataAttrsFromApi = (annotationsPages: PageInfo[]) => {
    const result: Record<number, Array<CategoryDataAttributeWithValue>> = {};

    annotationsPages.forEach((page) => {
        page.objs.forEach(({ id, data }) => {
            if (id && data && data.dataAttributes) {
                result[id] = data.dataAttributes;
            }
        });
    });

    return result;
};

export const mapAnnotationPagesFromApi = (
    annotationsPages: PageInfo[],
    getAnnotationLabels: (
        pageNum: number,
        ann: Annotation,
        category?: Category
    ) => AnnotationLabel[],
    categories?: Category[]
): Record<number, Annotation[]> => {
    const result: Record<number, Annotation[]> = {};
    annotationsPages.forEach((page) => {
        const pageAnnotations = page.objs.map((obj) => {
            const category = categories?.find((category) => category.id == obj.category);
            const ann = mapAnnotationFromApi(obj, category);
            return {
                ...ann,
                labels: getAnnotationLabels(page.page_num, ann, category)
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
        const filteredAnnotations = pageAnnotations.filter((el) => el.boundType !== 'table_cell');
        result[page.page_num] = [...(result[page.page_num] ?? []), ...filteredAnnotations];
    });
    return result;
};

const mapTokenFromApi = (obj: PageInfoObjs, id: number, scale: number): PageToken => {
    return {
        id,
        text: obj.text!,
        ...bboxToBound(obj.bbox, scale)
    };
};

export const mapTokenPagesFromApi = (
    tokenPages: PageInfo[],
    scale: number
): Record<number, PageToken[]> => {
    const res: Record<number, PageToken[]> = {};
    tokenPages.forEach((pageInfo) => {
        res[pageInfo.page_num] = pageInfo.objs.map((obj, index) => {
            return mapTokenFromApi(obj, index, scale);
        });
    });
    return res;
};
