import { DropSpot, Text, Blocker, Panel } from '@epam/loveship';
import { useAddFilesToDatasetMutation } from 'api/hooks/datasets';
import { useUploadFilesMutation } from 'api/hooks/documents';
import { Dataset } from 'api/typings';
import { DatasetWithFiles } from 'components/dataset/dataset-choose-form';
import { DropZone } from 'components/file-upload/drop-zone/drop-zone';
import React, { FC, useState } from 'react';
import { useNotifications } from 'shared/components/notifications';
import { getError } from 'shared/helpers/get-error';

type DocumentsDropZoneType = {
    dataset?: Dataset | null;
    children?: React.ReactNode;
};
export const DocumentsDropZone: FC<DocumentsDropZoneType> = ({ dataset, children }) => {
    const [isLoading, setIsLoading] = useState<boolean>(false);

    const uploadFilesMutation = useUploadFilesMutation();
    const addFilesToDatasetMutation = useAddFilesToDatasetMutation();
    const { notifyError, notifySuccess } = useNotifications();

    const uploadFilesHandler = async (files: File[]) => {
        try {
            setIsLoading(true);
            const responses = await uploadFilesMutation.mutateAsync(files);
            const filesIds: Array<number> = [];
            for (const response of responses) {
                filesIds.push(response.id);
                notifySuccess(<Text>{response.message}</Text>);
            }
            if (dataset) {
                const datasetWithFiles: DatasetWithFiles = {
                    name: dataset.name,
                    objects: filesIds
                };
                await addFilesToDatasetMutation.mutateAsync(datasetWithFiles);
            }
        } catch (error) {
            notifyError(<Text>{getError(error)}</Text>);
        } finally {
            setIsLoading(false);
        }
    };
    return (
        <>
            <Panel style={{ height: '100%', width: '100%' }}>
                <DropSpot
                    onFilesDropped={uploadFilesHandler}
                    render={({
                        eventHandlers: { onDragEnter, onDrop, onDragLeave, onDragOver }
                    }) => (
                        <DropZone
                            onDragEnter={onDragEnter}
                            onDrop={onDrop}
                            onDragLeave={onDragLeave}
                            onDragOver={onDragOver}
                        >
                            {children}
                        </DropZone>
                    )}
                ></DropSpot>

                {isLoading && <Blocker isEnabled={isLoading} />}
            </Panel>
        </>
    );
};
