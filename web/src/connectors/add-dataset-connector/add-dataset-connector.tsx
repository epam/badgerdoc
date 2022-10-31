import React, { FC } from 'react';

import { DatasetAddForm, DatasetValues } from 'components/dataset/dataset-add-form';
import { ErrorNotification, SuccessNotification, Text } from '@epam/loveship';

import { INotification, useUuiContext } from '@epam/uui';
import { useAddDatasetMutation } from 'api/hooks/datasets';
import SidebarButton from 'shared/components/sidebar/sidebar-button/sidebar-button';
import { getError } from 'shared/helpers/get-error';

interface AddDatasetConnectorProps {
    onCreated: () => void;
}

const AddDatasetConnector: FC<AddDatasetConnectorProps> = ({ onCreated }) => {
    const svc = useUuiContext();
    const mutation = useAddDatasetMutation();
    const onSaveDataset = async (dataset: DatasetValues) => {
        let createdDataset;
        try {
            createdDataset = await mutation.mutateAsync(dataset.name);
            return {
                form: createdDataset
            };
        } catch (err) {
            svc.uuiNotifications.show(
                (props: INotification) => (
                    <ErrorNotification {...props}>
                        <Text>{getError(err)}</Text>
                    </ErrorNotification>
                ),
                { duration: 2 }
            );
            return {
                form: createdDataset,
                validation: {
                    isInvalid: true
                }
            };
        }
    };
    const showModal = () => {
        return svc.uuiModals
            .show<DatasetValues>((props) => (
                <DatasetAddForm onSaveDataset={onSaveDataset} {...props} />
            ))
            .then(() => {
                svc.uuiNotifications.show(
                    (props: INotification) => (
                        <SuccessNotification {...props}>
                            <Text>Data has been saved!</Text>
                        </SuccessNotification>
                    ),
                    { duration: 2 }
                );
                onCreated();
            });
    };

    return <SidebarButton onClick={showModal} caption="Add new dataset" />;
};

export default AddDatasetConnector;
