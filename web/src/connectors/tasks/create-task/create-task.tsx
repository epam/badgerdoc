import React, { FC, useCallback } from 'react';

import { IModal } from '@epam/uui';
import { ModalBlocker, ModalWindow, Text } from '@epam/loveship';
import { TaskModel } from 'api/typings/tasks';
import { FileDocument, Filter, Operators, ResponseError, User } from 'api/typings';
import { documentsFetcher } from 'api/hooks/documents';
import { useEntity } from '../../../shared/hooks/use-entity';
import { usersFetcher } from 'api/hooks/users';
import { useCreateNewTaskMutation } from 'api/hooks/tasks';
import { CreateTaskForm } from 'components/task/create-task-form';
import { useNotifications } from 'shared/components/notifications';

type FormTaskModel = Partial<
    Pick<TaskModel, 'file_id' | 'user_id' | 'pages' | 'is_validation' | 'deadline'>
>;

interface ICreateNewTaskProps extends IModal<object> {
    annotatorIds: Array<string>;
    fileIds: Array<number>;
    jobId?: number;
}

export const CreateTask: FC<ICreateNewTaskProps> = ({
    jobId,
    fileIds,
    annotatorIds,
    ...modalProps
}) => {
    const mutation = useCreateNewTaskMutation();
    const { notifySuccess, notifyError } = useNotifications();

    const fileFilters: Filter<keyof FileDocument>[] = [
        { value: fileIds, operator: Operators.IN, field: 'id' }
    ];

    const annotatorsFilters: Filter<keyof User>[] = [
        { value: annotatorIds, operator: Operators.IN, field: 'id' }
    ];

    const { dataSource: filesDataSource } = useEntity<FileDocument, number>(
        documentsFetcher,
        fileFilters
    );

    const { dataSource: annotatorsDataSource } = useEntity<User, string>(
        usersFetcher,
        annotatorsFilters
    );

    const onTaskCreation = useCallback(
        async (task) => {
            try {
                const response = await mutation.mutateAsync({
                    ...task,
                    job_id: jobId,
                    pages: task.pages.map(Number),
                    deadline: `${task.deadline}`
                });
                notifySuccess(
                    <>
                        <Text fontSize="18" font="sans-semibold">
                            Success!
                        </Text>
                        <Text>{`Task is created with id=${response.id}`}</Text>
                    </>
                );
            } catch (error) {
                const errorObject: ResponseError = JSON.parse((error as Error).message);
                notifyError(
                    <>
                        <Text fontSize="18" font="sans-semibold">
                            {errorObject.statusText}
                        </Text>
                        <Text>{errorObject.message}</Text>
                    </>
                );
                console.error('Error details:', errorObject.details);
                throw error;
            }
        },
        [jobId]
    );

    return (
        <ModalBlocker {...modalProps} isActive={false} disallowClickOutside blockerShadow="dark">
            <ModalWindow>
                <CreateTaskForm
                    onCancelButton={modalProps.abort}
                    onSuccess={(task: FormTaskModel) => modalProps.success(task)}
                    onTaskCreation={onTaskCreation}
                    filesDataSource={filesDataSource}
                    annotatorsDataSource={annotatorsDataSource}
                />
            </ModalWindow>
        </ModalBlocker>
    );
};
