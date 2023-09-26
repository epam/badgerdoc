import React, {
    Dispatch,
    MutableRefObject,
    SetStateAction,
    useCallback,
    useEffect,
    useMemo,
    useState
} from 'react';
import { difference, isEmpty } from 'lodash';

import { Task, TTaskUsers } from 'api/typings/tasks';
import { CategoryDataAttributeWithValue, PageInfo, ValidationType } from 'api/typings';

import { AnnotationsResponse, useAddAnnotationsMutation } from 'api/hooks/annotations';
import { useGetPageSummary, useSetTaskFinishedMutation, useSetTaskState } from 'api/hooks/tasks';
import {
    FinishTaskValidationModal,
    TaskValidationValues
} from '../../components/task/task-modal/task-validation-modal';
import { ApiError } from 'api/api-error';
import { Annotation, PageToken } from 'shared';
import { PageSize } from 'shared/components/document-pages/document-pages';
import { mapModifiedAnnotationPagesToApi } from './task-annotator-utils';

import { useUuiContext } from '@epam/uui';
import { showError } from 'shared/components/notifications';
import { getError } from 'shared/helpers/get-error';
import { Job } from 'api/typings/jobs';

export type ValidationParams = {
    refetchLatestAnnotations: (pageNumbers: number[]) => Promise<void>;
    latestAnnotationsResultData: AnnotationsResponse | undefined;
    task?: Task;
    job?: Job;
    currentPage: number;
    pageNumbers: number[];
    onCloseDataTab: () => void;
    isOwner: boolean;
    taskUsers: MutableRefObject<TTaskUsers>;
    onSaveTask: () => void;
    annotationsChanges: Record<number, Annotation[]>;
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
    refetchLatestAnnotations,
    latestAnnotationsResultData,
    task,
    job,
    currentPage,
    pageNumbers,
    taskUsers,
    isOwner,
    onCloseDataTab,
    onSaveTask,
    annotationsChanges,
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
    const [notProcessedPagesFromApi, setNotProcessedPagesFromApi] = useState<number[]>([]);
    const [touchedPages, setTouchedPages] = useState<number[]>([]);
    const [annotationSaved, setAnnotationSaved] = useState(false);

    // TODO: there is a pages.not_processed property which is not calculated on BE side
    // in the right way. In order to not wait this fix, the logic
    // is implemented on FE side. Need to investigate this on BE side and fix it's behavior
    // if it's needed
    const notProcessedPages = useMemo(
        () =>
            job?.validation_type === ValidationType.extensiveCoverage
                ? notProcessedPagesFromApi
                : difference(pageNumbers, validPages, invalidPages),
        [job, notProcessedPagesFromApi, pageNumbers, validPages, invalidPages]
    );

    const setPages = useCallback(
        (setPagesState: React.Dispatch<React.SetStateAction<number[]>>) => {
            setPagesState((pagesArr) =>
                pagesArr.includes(currentPage)
                    ? pagesArr.filter((page) => page !== currentPage)
                    : pagesArr
            );
        },
        [currentPage]
    );

    const svc = useUuiContext();

    const { data: pages } = useGetPageSummary(
        { taskId: task?.id, taskType: task?.is_validation },
        { enabled: Boolean(task) }
    );

    const finishTaskMutation = useSetTaskFinishedMutation();

    const onSaveForm = useCallback(
        async ({ option_edited, option_invalid }: TaskValidationValues) => {
            if (!task || (!option_invalid && !option_edited)) return;

            try {
                await finishTaskMutation.mutateAsync({
                    taskId: task?.id,
                    options: {
                        option_edited,
                        option_invalid
                    }
                });

                await useSetTaskState({ id: task?.id, eventType: 'closed' });
            } catch (error) {
                showError(getError(error));
            }
        },
        [finishTaskMutation, task]
    );

    const onSaveValidForm = useCallback(async () => {
        if (task) {
            await finishTaskMutation.mutateAsync({ taskId: task?.id });
            await useSetTaskState({ id: task?.id, eventType: 'closed' });
        }
    }, [finishTaskMutation, task]);

    useEffect(() => {
        if (pages) {
            setValidPages(pages.validated);
            setInvalidPages(pages.failed_validation_pages);
            setNotProcessedPagesFromApi(pages.not_processed);
        }
    }, [pages]);

    const allValid =
        isEmpty(invalidPages) &&
        isEmpty(editedPages) &&
        isEmpty(notProcessedPages) &&
        !isEmpty(validPages);

    const allValidated = isEmpty(notProcessedPages);

    const onValidClick = useCallback(() => {
        setPages(setInvalidPages);
        setPages(setNotProcessedPagesFromApi);
        setValidPages((prevValidPages) => [...prevValidPages, currentPage]);
        setAnnotationSaved(false);
    }, [setPages, currentPage]);

    const onInvalidClick = useCallback(() => {
        setPages(setValidPages);
        setPages(setNotProcessedPagesFromApi);
        setInvalidPages((prevInvalidPages) => [...prevInvalidPages, currentPage]);
        setAnnotationSaved(false);
    }, [setPages, currentPage]);

    const onClearTouchedPages = useCallback(async () => {
        setTouchedPages([]);
    }, []);

    const onAddTouchedPage = useCallback(() => {
        !touchedPages.includes(currentPage)
            ? setTouchedPages([...touchedPages, currentPage])
            : () => {};
    }, [touchedPages, currentPage]);

    const onEditClick = useCallback(() => {
        setEditedPages((prevEditedPages) => [...prevEditedPages, currentPage]);
        setPages(setInvalidPages);
        setAnnotationSaved(false);
    }, [currentPage, setPages]);

    const onCancelClick = useCallback(() => {
        onCloseDataTab();
        setPages(setEditedPages);
        setInvalidPages((prevInvalidPages) => [...prevInvalidPages, currentPage]);
    }, [onCloseDataTab, setPages, currentPage]);

    const addAnnotationMutation = useAddAnnotationsMutation();

    const onSaveEditClick = useCallback(async () => {
        if (!task || !latestAnnotationsResultData || !tokenPages) return;
        setPages(setInvalidPages);
        setPages(setValidPages);
        setPages(setEditedPages);

        let { revision } = latestAnnotationsResultData;
        const pages = mapModifiedAnnotationPagesToApi(
            editedPages,
            annotationsChanges,
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

            refetchLatestAnnotations(pages.map(({ page_num }) => page_num));
            setAnnotationSaved(true);
        } catch (error) {
            onSaveTaskError(error as ApiError);
        }
    }, [
        addAnnotationMutation,
        annDataAttrs,
        annotationsChanges,
        editedPages,
        refetchLatestAnnotations,
        latestAnnotationsResultData,
        onCloseDataTab,
        onSaveTaskError,
        onSaveTaskSuccess,
        pageSize,
        setPages,
        task,
        tokenPages,
        tokensByPages
    ]);

    const showValidationModal = useCallback(() => {
        svc.uuiModals.show<TaskValidationValues>((props) => (
            <FinishTaskValidationModal
                onSaveForm={onSaveForm}
                allValid={allValid}
                allUsers={taskUsers.current}
                currentUser={task?.user_id || ''}
                isOwner={isOwner}
                invalidPages={invalidPages.length}
                editedPageCount={editedPages.length}
                validSave={onSaveValidForm}
                onRedirectAfterFinish={onRedirectAfterFinish}
                {...props}
            />
        ));
    }, [
        allValid,
        editedPages.length,
        invalidPages.length,
        isOwner,
        onRedirectAfterFinish,
        onSaveForm,
        onSaveValidForm,
        svc.uuiModals,
        task?.user_id,
        taskUsers
    ]);

    const onFinishValidation = useCallback(async () => {
        if (!annotationSaved) {
            await onSaveTask();
        }
        showValidationModal();
    }, [annotationSaved, onSaveTask, showValidationModal]);

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
            onFinishValidation,
            onSaveEditClick
        ]
    );
};
