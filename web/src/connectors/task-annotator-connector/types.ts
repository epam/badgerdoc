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
    AnnotationLinksBoundType,
    Maybe,
    PageToken,
    PaperToolParams,
    TableGutterMap,
    ToolNames
} from 'shared';
import { SyncScrollValue } from 'shared/hooks/use-sync-scroll';
import { PageSize } from '../../shared/components/document-pages/document-pages';
import { DocumentLinksValue } from './use-document-links';
import { ValidationValues } from './use-validation';
import { AnnotationsByUserObj } from 'api/hooks/annotations';
import { Dispatch, SetStateAction } from 'react';

type TAnnotationHandlers = {
    onSplitAnnotationSelected: (scale: number, userId: string, annotation?: Annotation) => void;
    onSplitLinkSelected: (
        fromOriginalAnnotationId: string | number,
        originalLink: Link,
        annotations: Annotation[]
    ) => void;
    onAnnotationCreated: (pageNum: number, annotation: Annotation) => void;
    onAnnotationDeleted: (pageNum: number, annotationId: string | number) => void;
    onAnnotationEdited: (
        pageNum: number,
        annotationId: string | number,
        changes: Partial<Annotation>
    ) => void;
    onAnnotationDoubleClick: (annotation: Annotation) => void;
    onAnnotationCopyPress: (pageNum: number, annotationId: string | number) => void;
    onAnnotationCutPress: (pageNum: number, annotationId: string | number) => void;
    onAnnotationPastePress: (pageSize: PageSize, pageNum: number) => void;
    onAnnotationUndoPress: () => void;
    onAnnotationRedoPress: () => void;
};

export type ContextValue = TAnnotationHandlers &
    SyncScrollValue &
    DocumentLinksValue &
    Omit<ValidationValues, 'allValid' | 'setAnnotationSaved'> & {
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
        setPageSize: (pS: any) => void;
        tabValue: string;
        selectionType: AnnotationBoundType | AnnotationLinksBoundType | ToolNames;
        selectedTool: ToolNames;
        onChangeSelectedTool: (t: ToolNames) => void;
        tableMode: boolean;
        isNeedToSaveTable: {
            gutters: Maybe<TableGutterMap>;
            cells: Maybe<Annotation[]>;
        };
        setIsNeedToSaveTable: (b: {
            gutters: Maybe<TableGutterMap>;
            cells: Maybe<Annotation[]>;
        }) => void;
        isCategoryDataEmpty: boolean;
        annDataAttrs: Record<string, Array<CategoryDataAttributeWithValue>>;
        externalViewer: ExternalViewerState;
        onChangeSelectionType: (
            newType: AnnotationBoundType | AnnotationLinksBoundType | ToolNames
        ) => void;
        onCategorySelected: (category: Category) => void;
        onSaveTask: () => void;
        onExternalViewerClose: () => void;
        onAnnotationTaskFinish: () => void;
        onLinkDeleted: (pageNum: number, annotationId: string | number, link: Link) => void;
        onCurrentPageChange: (page: number) => void;
        onClearModifiedPages: () => void;
        onEmptyAreaClick: () => void;
        setTabValue: (value: string) => void;
        onDataAttributesChange: (elIndex: number, value: string) => void;
        tableCellCategory: string | number | undefined;
        setTableCellCategory: (s: string | number | undefined) => void;
        selectedToolParams: PaperToolParams;
        setSelectedToolParams: (nt: PaperToolParams) => void;
        setSelectedAnnotation: (annotation: Annotation | undefined) => void;
        selectedLabels?: Label[];
        onLabelsSelected: (labels: Label[], pickedLabels: string[]) => void;
        setSelectedLabels: (labels: Label[]) => void;
        latestLabelsId: string[];
        isDocLabelsModified: boolean;
        getJobId: () => number | undefined;
        // linksFromApi?: DocumentLink[];
        setCurrentDocumentUserId: (userId?: string) => void;
        currentDocumentUserId?: string;
        onSplitAnnotationSelected: (scale: number, userId: string, annotation?: Annotation) => void;
        isSplitValidation?: boolean;
        userPages: AnnotationsByUserObj[];
        annotationsByUserId: Record<string, Annotation[]>;
        categoriesByUserId: Record<string, Label[]>;
    };

export type TUseAnnotationHandlersProps = {
    allAnnotations: ContextValue['allAnnotations'];
    setAllAnnotations: Dispatch<SetStateAction<Record<string, Annotation[]>>>;
    setModifiedPages: Dispatch<SetStateAction<number[]>>;
    setTableMode: Dispatch<SetStateAction<boolean>>;
    setSelectedAnnotation: ContextValue['setSelectedAnnotation'];
    setTabValue: ContextValue['setTabValue'];
    categories: ContextValue['categories'];
    setIsCategoryDataEmpty: Dispatch<SetStateAction<boolean>>;
    setAnnDataAttrs: Dispatch<SetStateAction<Record<string, CategoryDataAttributeWithValue[]>>>;
    currentPage: ContextValue['currentPage'];
    annotationsByUserId: ContextValue['annotationsByUserId'];
    setExternalViewer: Dispatch<SetStateAction<ExternalViewerState>>;
    createAnnotation: (pageNum: number, annData: Annotation, category?: Category) => Annotation;
    onAddTouchedPage: ContextValue['onAddTouchedPage'];
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
