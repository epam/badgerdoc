import { Link } from 'api/typings';
import { Annotation } from 'shared';

export type TAnnotationProps = Annotation & {
    index: number;
    incomingLinks?: Annotation['links'];
    annotationNameById: Record<string, string>;
    onSelect: (index: number) => void;
    onSelectById: (id: Annotation['id']) => void;
    selectedAnnotationId?: Annotation['id'];
    isEditable: boolean;
    onLinkDeleted: (pageNum: number, annotationId: Annotation['id'], link: Link) => void;
    onCloseIconClick: (pageNum: number, annotationId: Annotation['id']) => void;
};
