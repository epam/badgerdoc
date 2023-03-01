import React from 'react';
import { useDeleteDatasetMutation } from 'api/hooks/datasets';
import { Dataset } from 'api/typings';
import { SidebarRowSelection } from 'shared/components/sidebar/sidebar-row-selection/sidebar-row-selection';
import { getError } from 'shared/helpers/get-error';
import { DeleteDataset } from '../delete-dataset/delete-dataset';

import { FlexRow, LinkButton, FlexSpacer, ErrorNotification, Text } from '@epam/loveship';
import { useUuiContext, INotification } from '@epam/uui';
import styles from './dataset-row.module.scss';

type DatasetRowProps = {
    dataset: Dataset;
    onDatasetClick: (dataset: Dataset) => void;
    activeDataset: Dataset | null | undefined;
};

export const DatasetRow = ({ dataset, onDatasetClick, activeDataset }: DatasetRowProps) => {
    const mutationDeleteDataset = useDeleteDatasetMutation();
    const svc = useUuiContext();

    const handleSelectDataset = (dataset: Dataset) => {
        onDatasetClick(dataset);
    };
    const handleDatasetDelete = async (dataset: Dataset) => {
        try {
            await mutationDeleteDataset.mutateAsync(dataset.name);
        } catch (err) {
            svc.uuiNotifications.show(
                (props: INotification) => (
                    <ErrorNotification {...props}>
                        <Text>{getError(err)}</Text>
                    </ErrorNotification>
                ),
                { duration: 2 }
            );
        }
    };
    return (
        <SidebarRowSelection
            entity={dataset}
            activeEntity={activeDataset}
            onEntitySelect={handleSelectDataset}
        >
            <FlexRow padding="18" key={dataset.name} cx={`flex align-center`}>
                <LinkButton
                    caption={`${dataset.name} (${dataset.count})`}
                    cx={styles.text}
                    size="42"
                    color="night900"
                />

                <DeleteDataset
                    dataset={dataset}
                    onDeleteDataset={handleDatasetDelete}
                    className={styles.deleteDataset}
                />

                <FlexSpacer />
            </FlexRow>
        </SidebarRowSelection>
    );
};
