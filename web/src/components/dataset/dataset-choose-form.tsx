import React, { FC, ReactNode, useState, useCallback } from 'react';
import {
    FormSaveResponse,
    IModal,
    Metadata,
    RenderFormProps,
    useUuiContext,
    ILens
} from '@epam/uui';
import {
    ModalBlocker,
    ModalWindow,
    FlexSpacer,
    ModalHeader,
    FlexRow,
    LabeledInput,
    Button,
    ScrollBars,
    ModalFooter,
    Panel,
    Form
} from '@epam/loveship';
import { Dataset } from 'api/typings';
import { datasetsFetcher } from 'api/hooks/datasets';
import { useEntity } from 'shared/hooks/use-entity';
import { DatasetPicker } from 'components';

export interface DatasetWithFiles {
    name: string;
    objects: number[];
}

interface IProps extends IModal<DatasetWithFiles> {
    onChooseDataset: (
        dataset: DatasetWithFiles
    ) => Promise<FormSaveResponse<DatasetWithFiles> | void>;
}

export const DatasetChooseForm: FC<IProps> = ({ onChooseDataset, ...modalProps }) => {
    const svc = useUuiContext();
    const [selectedDataset, setDataset] = useState<Dataset>();
    const [dataset] = useState<DatasetWithFiles>({
        name: '',
        objects: []
    });
    const { dataSource } = useEntity<Dataset, Dataset>(datasetsFetcher);
    const getMetaData = (): Metadata<DatasetWithFiles> => ({
        props: {
            name: { isRequired: true }
        }
    });
    const onDatasetSelect = useCallback(
        (dataset, lens: ILens<DatasetWithFiles>) => {
            lens.prop('name').set(dataset?.name);
            setDataset(dataset);
        },
        [selectedDataset]
    );

    const renderForm = ({ lens, save }: RenderFormProps<DatasetWithFiles>): ReactNode => {
        return (
            <>
                <Panel>
                    <FlexRow padding="24" vPadding="12">
                        <LabeledInput label="Datasets" {...lens.prop('name').toProps()}>
                            <DatasetPicker
                                onDatasetSelect={(dataset) => onDatasetSelect(dataset, lens)}
                                dataSource={dataSource}
                                title={(<h4>Datasets</h4>) as unknown as HTMLElement}
                                dataset={selectedDataset}
                            />
                        </LabeledInput>
                    </FlexRow>
                </Panel>
                <ModalFooter>
                    <FlexSpacer />
                    <Button
                        color="sky"
                        fill="white"
                        onClick={() => handleLeave().then(modalProps.abort)}
                        caption="Cancel"
                    />
                    <Button color="sky" caption="Choose" onClick={save} />
                </ModalFooter>
            </>
        );
    };

    const handleLeave = () => svc.uuiLocks.acquire(() => Promise.resolve());

    return (
        <ModalBlocker
            {...modalProps}
            abort={() => handleLeave().then(modalProps.abort)}
            blockerShadow="dark"
        >
            <ModalWindow>
                <ModalHeader title="Choose dataset" onClose={modalProps.abort} />
                <ScrollBars>
                    <Form<DatasetWithFiles>
                        value={dataset}
                        onSave={onChooseDataset}
                        onSuccess={(dataset) => modalProps.success(dataset)}
                        renderForm={renderForm}
                        getMetadata={getMetaData}
                    />
                    <FlexSpacer />
                </ScrollBars>
            </ModalWindow>
        </ModalBlocker>
    );
};
