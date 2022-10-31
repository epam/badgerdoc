import { CategoryDataAttrType } from 'api/typings';
import { AnnotationBoundType } from 'shared';

export type DocumentAnnotations = {
    revision: string;
    user: string;
    pipeline: number;
    date: string;
    pages: DocumentAnnotationsPage[];
};

type DocumentAnnotationsPage = {
    page_num: number;
    size: { width: number; height: number };
    objs: DocumentAnnotationObj[];
    isValidated: boolean;
};

type DocumentAnnotationObj = {
    id: number;
    category: number;
    bbox: number[];
    type: AnnotationBoundType;
};
export type ExternalViewerPopupProps = {
    onClose: Function;
    valueAttr: string;
    typeAttr: CategoryDataAttrType;
    nameAttr: string;
};
export type DocumentAnnotationsResponse = DocumentAnnotations;
