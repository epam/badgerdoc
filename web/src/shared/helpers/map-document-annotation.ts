import { DocumentAnnotationsResponse } from '../../api/typings/annotations';
import type { Annotation } from '../components';
import { bboxToBound } from './bbox-to-bound';

export const mapDocumentAnnotation = (
    annotationData: DocumentAnnotationsResponse,
    categories: Map<string, { color: string; label: string }>
): { [k: number]: Annotation[] } => {
    const annotations = {} as { [k: number]: Annotation[] };

    try {
        annotationData.pages.forEach((item) => {
            if (!annotations[item.page_num]) {
                annotations[item.page_num] = [] as Annotation[];
            }
            item.objs.forEach((it) => {
                annotations[item.page_num].push({
                    id: it.id,
                    //@ts-ignore
                    color: categories.get(it.category).color,
                    category: it.category,
                    //@ts-ignore
                    label: categories.get(it.category).label,
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
