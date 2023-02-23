import { AnnotationsResponse, useAddAnnotationsMutation } from 'api/hooks/annotations';
import { useGetValidatedPages, useSetTaskFinishedMutation, useSetTaskState } from 'api/hooks/tasks';
import { Task } from 'api/typings/tasks';
import {
    FinishTaskValidationModal,
    TaskValidationValues
} from '../../components/task/task-modal/task-validation-modal';
import React, {
    Dispatch,
    MutableRefObject,
    SetStateAction,
    useCallback,
    useEffect,
    useMemo,
    useState
} from 'react';
import { useUuiContext } from '@epam/uui';
import { CategoryDataAttributeWithValue, PageInfo, User } from 'api/typings';
import { UseQueryResult } from 'react-query';
import { ApiError } from 'api/api-error';
import { mapModifiedAnnotationPagesToApi } from './task-annotator-utils';
import { Annotation, PageToken } from 'shared';
import { PageSize } from 'shared/components/document-pages/document-pages';
import { isEmpty } from 'lodash';

export type ValidationParams = {
    latestAnnotationsResult: UseQueryResult<AnnotationsResponse, unknown>;
    task?: Task;
    currentPage: number;
    onCloseDataTab: () => void;
    isOwner: boolean;
    sortedUsers: MutableRefObject<{ owners: User[]; annotators: User[]; validators: User[] }>;
    onSaveTask: () => void;
    allAnnotations: Record<number, Annotation[]>;
    tokensByPages: Record<number, PageToken[]>;
    tokenPages?: PageInfo[];
    annDataAttrs: Record<number, Array<CategoryDataAttributeWithValue>>;
    pageSize: PageSize;
    onRedirectAfterFinish: () => void;
    onSaveTaskSuccess: () => void;
    onSaveTaskError: (error: ApiError) => void;
};

export type ValidationValues = {
    validPages: number[];
    invalidPages: number[];
    editedPages: number[];
    touchedPages: number[];
    notProcessedPages: number[];
    allValid: boolean;
    allValidated: boolean;
    annotationSaved: boolean;
    onValidClick: () => void;
    onInvalidClick: () => void;
    onEditClick: () => void;
    onCancelClick: () => void;
    onClearTouchedPages: () => void;
    onAddTouchedPage: () => void;
    setValidPages: (pages: number[]) => void;
    onFinishValidation: () => void;
    onSaveEditClick: () => void;
    setAnnotationSaved: Dispatch<SetStateAction<boolean>>;
};

export const useValidation = ({
    latestAnnotationsResult,
    task,
    currentPage,
    sortedUsers,
    isOwner,
    onCloseDataTab,
    onSaveTask,
    allAnnotations,
    tokensByPages,
    tokenPages,
    annDataAttrs,
    pageSize,
    onRedirectAfterFinish,
    onSaveTaskSuccess,
    onSaveTaskError
}: ValidationParams) => {
    const [validPages, setValidPages] = useState<number[]>([]);
    const [invalidPages, setInvalidPages] = useState<number[]>([]);
    const [editedPages, setEditedPages] = useState<number[]>([]);
    const [notProcessedPages, setNotProcessedPages] = useState<number[]>([]);
    const [touchedPages, setTouchedPages] = useState<number[]>([]);
    const [annotationSaved, setAnnotationSaved] = useState(false);

    const setPages = (
        pagesArr: number[],
        setPagesState: React.Dispatch<React.SetStateAction<number[]>>
    ) => {
        if (pagesArr.includes(currentPage)) {
            const newIPages = pagesArr.filter((page) => page !== currentPage);
            setPagesState(newIPages);
        }
    };

    const svc = useUuiContext();

    const { data: pages } = useGetValidatedPages(
        { taskId: task?.id, taskType: task?.is_validation },
        { enabled: !!task }
    );
    const finishTaskMutation = useSetTaskFinishedMutation();
    const onSaveForm = async (formOptions: TaskValidationValues) => {
        if (task && (formOptions.option_invalid || formOptions.option_edited)) {
            await finishTaskMutation.mutateAsync({
                taskId: task?.id,
                options: {
                    option_edited: formOptions.option_edited,
                    option_invalid: formOptions.option_invalid
                }
            });

            await useSetTaskState({ id: task?.id, eventType: 'closed' });
            return { form: formOptions };
        }
    };

    const onSaveValidForm = async () => {
        if (task) {
            await finishTaskMutation.mutateAsync({ taskId: task?.id });
            await useSetTaskState({ id: task?.id, eventType: 'closed' });
            return {};
        }
    };
    useEffect(() => {
        if (pages) {
            setValidPages(pages.validated);
            setInvalidPages(pages.failed_validation_pages);
            setNotProcessedPages(pages.not_processed);
        }
    }, [pages]);

    const allValid =
        isEmpty(invalidPages) &&
        isEmpty(editedPages) &&
        isEmpty(notProcessedPages) &&
        !isEmpty(validPages);

    const allValidated = isEmpty(notProcessedPages);

    const onValidClick = useCallback(() => {
        setPages(invalidPages, setInvalidPages);
        setPages(notProcessedPages, setNotProcessedPages);
        setValidPages([...validPages, currentPage]);
        setAnnotationSaved(false);
    }, [invalidPages, validPages, currentPage, notProcessedPages]);

    const onInvalidClick = useCallback(() => {
        setPages(validPages, setValidPages);
        setPages(notProcessedPages, setNotProcessedPages);
        setInvalidPages([...invalidPages, currentPage]);
        setAnnotationSaved(false);
    }, [invalidPages, validPages, currentPage, notProcessedPages]);

    const onClearTouchedPages = useCallback(async () => {
        setTouchedPages([]);
    }, []);

    const onAddTouchedPage = useCallback(() => {
        !touchedPages.includes(currentPage)
            ? setTouchedPages([...touchedPages, currentPage])
            : () => {};
    }, [touchedPages, currentPage]);

    const onEditClick = useCallback(() => {
        setEditedPages([...editedPages, currentPage]);
        setPages(invalidPages, setInvalidPages);
        setAnnotationSaved(false);
    }, [editedPages, invalidPages, currentPage]);

    const onCancelClick = useCallback(() => {
        onCloseDataTab();
        setPages(editedPages, setEditedPages);
        setInvalidPages([...invalidPages, currentPage]);
    }, [editedPages, invalidPages, currentPage]);

    const addAnnotationMutation = useAddAnnotationsMutation();

    const onSaveEditClick = async () => {
        if (!task || !latestAnnotationsResult.data || !tokenPages) return;
        setPages(invalidPages, setInvalidPages);
        setPages(validPages, setValidPages);

        let { revision } = latestAnnotationsResult.data;
        const pages = mapModifiedAnnotationPagesToApi(
            editedPages,
            allAnnotations,
            tokensByPages,
            tokenPages,
            annDataAttrs,
            pageSize
        );

        onCloseDataTab();

        if (!task.id) {
            return;
        }

        try {
            await addAnnotationMutation.mutateAsync({
                taskId: task.id,
                pages,
                userId: task.user_id,
                revision,
                validPages: [],
                invalidPages: []
            });
            onCloseDataTab();
            onSaveTaskSuccess();

            latestAnnotationsResult.refetch();
            setAnnotationSaved(true);
        } catch (error) {
            onSaveTaskError(error as ApiError);
        }
    };

    const onFinishValidation = async () => {
        if (!annotationSaved) {
            await onSaveTask();
        }
        showValidationModal();
    };

    const showValidationModal = () => {
        svc.uuiModals.show<TaskValidationValues>((props) => (
            <FinishTaskValidationModal
                onSaveForm={onSaveForm}
                allValid={allValid}
                allUsers={sortedUsers.current}
                currentUser={task?.user_id || ''}
                isOwner={isOwner}
                invalidPages={invalidPages.length}
                editedPageCount={editedPages.length}
                validSave={onSaveValidForm}
                onRedirectAfterFinish={onRedirectAfterFinish}
                {...props}
            />
        ));
    };
    return useMemo(
        () => ({
            validPages,
            invalidPages,
            editedPages,
            touchedPages,
            notProcessedPages,
            allValid,
            allValidated,
            annotationSaved,
            onValidClick,
            onInvalidClick,
            onEditClick,
            onAddTouchedPage,
            onClearTouchedPages,
            onCancelClick,
            setValidPages,
            onFinishValidation,
            onSaveEditClick,
            setAnnotationSaved
        }),
        [
            validPages,
            invalidPages,
            editedPages,
            touchedPages,
            notProcessedPages,
            allValid,
            allValidated,
            annotationSaved,
            onValidClick,
            onInvalidClick,
            onEditClick,
            onAddTouchedPage,
            onClearTouchedPages,
            onCancelClick,
            setValidPages
        ]
    );
};
