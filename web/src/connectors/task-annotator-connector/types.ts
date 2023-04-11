import { Task } from 'api/typings/tasks';
import { ApiError } from 'api/api-error';
import {
    Category,
    CategoryDataAttributeWithValue,
    ExternalViewerState,
    Label,
    Link
} from 'api/typings';
import { Job } from 'api/typings/jobs';
import { FileMetaInfo } from 'pages/document/document-page-sidebar-content/document-page-sidebar-content';

import {
    Annotation,
    AnnotationBoundType,
    AnnotationImageToolType,
    AnnotationLinksBoundType,
    Maybe,
    PageToken,
    PaperToolParams,
    TableGutterMap
} from 'shared';
import { SyncScrollValue } from 'shared/hooks/use-sync-scroll';
import { PageSize } from '../../shared/components/document-pages/document-pages';
import { DocumentLinksValue } from './use-document-links';
import { ValidationValues } from './use-validation';
import { SplitValidationValue } from './use-split-validation';

export type ContextValue = SplitValidationValue &
    SyncScrollValue &
    DocumentLinksValue &
    Omit<ValidationValues, 'allValid' | 'setValidPages' | 'setAnnotationSaved'> & {
        task?: Task;
        job?: Job;
        categories?: Category[];
        selectedCategory?: Category;
        selectedAnnotation?: Annotation;
        fileMetaInfo: FileMetaInfo;
        tokensByPages: Record<string, PageToken[]>;
        allAnnotations?: Record<string, Annotation[]>;
        pageNumbers: number[];
        currentPage: number;
        modifiedPages: number[];
        pageSize?: { width: number; height: number };
        tabValue: string;
        selectionType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType;
        selectedTool: AnnotationImageToolType;
        onChangeSelectedTool: (t: AnnotationImageToolType) => void;
        tableMode: boolean;
        isNeedToSaveTable: {
            gutters?: TableGutterMap;
            cells?: Annotation[];
        };
        setIsNeedToSaveTable: (b: {
            gutters: Maybe<TableGutterMap>;
            cells: Maybe<Annotation[]>;
        }) => void;
        isCategoryDataEmpty: boolean;
        annDataAttrs: Record<string, Array<CategoryDataAttributeWithValue>>;
        externalViewer: ExternalViewerState;
        onChangeSelectionType: (
            newType: AnnotationBoundType | AnnotationLinksBoundType | AnnotationImageToolType
        ) => void;
        onCategorySelected: (category: Category) => void;
        onSaveTask: () => void;
        onExternalViewerClose: () => void;
        onAnnotationTaskFinish: () => void;
        onAnnotationCreated: (pageNum: number, annotation: Annotation) => void;
        onAnnotationDeleted: (pageNum: number, annotationId: string | number) => void;
        onAnnotationEdited: (
            pageNum: number,
            annotationId: string | number,
            changes: Partial<Annotation>
        ) => void;
        onLinkDeleted: (pageNum: number, annotationId: string | number, link: Link) => void;
        onCurrentPageChange: (page: number) => void;
        onClearModifiedPages: () => void;
        onEmptyAreaClick: () => void;
        onAnnotationDoubleClick: (annotation: Annotation) => void;
        onAnnotationCopyPress: (pageNum: number, annotationId: string | number) => void;
        onAnnotationCutPress: (pageNum: number, annotationId: string | number) => void;
        onAnnotationPastePress: (pageSize: PageSize, pageNum: number) => void;
        onAnnotationUndoPress: () => void;
        onAnnotationRedoPress: () => void;
        setTabValue: (value: string) => void;
        onDataAttributesChange: (elIndex: number, value: string) => void;
        tableCellCategory: string | number | undefined;
        setTableCellCategory: (s: string | number | undefined) => void;
        selectedToolParams: PaperToolParams;
        setSelectedToolParams: (nt: PaperToolParams) => void;
        setSelectedAnnotation: (annotation: Annotation | undefined) => void;
        selectedLabels?: Label[];
        onLabelsSelected: (labels: Label[]) => void;
        latestLabelsId: string[];
        isDocLabelsModified: boolean;
        getJobId: () => number | undefined;
        setCurrentDocumentUserId: (userId?: string) => void;
        currentDocumentUserId?: string;
    };

export type ProviderProps = {
    taskId?: number;
    fileMetaInfo?: FileMetaInfo;
    jobId?: number;
    revisionId?: string;
    onRedirectAfterFinish?: () => void;
    onSaveTaskSuccess?: () => void;
    onSaveTaskError?: (error: ApiError) => void;
};

export type UndoListAction = 'edit' | 'delete' | 'add';
