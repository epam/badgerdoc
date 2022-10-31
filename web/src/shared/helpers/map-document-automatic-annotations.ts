import { DocumentAnnotationsResponse } from '../../api/typings/annotations';
import type { Annotation } from '../components';
import { Category } from '../../api/typings';
import { bboxToBound } from './bbox-to-bound';

export const mapDocumentAutomaticAnnotation = (
    annotationData: DocumentAnnotationsResponse,
    categories: Category[]
): { [k: number]: Annotation[] } => {
    const annotations = {} as { [k: number]: Annotation[] };

    const normalizedCategories = categories.reduce((acc, item) => {
        if (!acc.has(item.id)) {
            acc.set(item.id, { color: item.metadata && item.metadata.color, label: item.name });
        }
        return acc;
    }, new Map());

    try {
        annotationData.pages.forEach((item) => {
            if (!annotations[item.page_num]) {
                annotations[item.page_num] = [] as Annotation[];
            }
            item.objs.forEach((it) => {
                annotations[item.page_num].push({
                    id: it.id,
                    color: normalizedCategories.get(it.category).color,
                    category: it.category,
                    label: normalizedCategories.get(it.category).label,
                    boundType: it.type || 'box',
                    bound: bboxToBound(it.bbox)
                });
            });
        });
        return annotations;
    } catch {
        return {} as { [k: number]: Annotation[] };
    }
};
