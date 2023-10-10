// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare, react-hooks/exhaustive-deps */
import React, { useCallback, useContext, useState } from 'react';
import { useHistory } from 'react-router';
import Wizard, {
    renderWizardButtons,
    WizardPropsStep
} from '../../shared/components/wizard/wizard/wizard';

import UploadWizardPreprocessor, {
    UploadWizardPreprocessorResult
} from '../../components/upload-wizard/preprocessor/upload-wizard-preprocessor';
import { DatasetWithFiles } from '../../components';
import { UploadFilesControl } from '../../components/upload-files-control/upload-files-control';
import { useUploadFilesMutation } from 'api/hooks/documents';
import { bondToDataset } from 'api/hooks/bonds';
import { useNotifications } from 'shared/components/notifications';
import { useAddDatasetMutation, useAddFilesToDatasetMutation } from '../../api/hooks/datasets';
import EditJobConnector from 'connectors/edit-job-connector/edit-job-connector';
import {
    DatasetWizardScreen,
    DatasetWizardScreenResult
} from '../../shared/components/wizard/dataset-wizard-screen/dataset-wizard-screen';
import { runPreprocessing } from '../../api/hooks/models';
import { getError } from 'shared/helpers/get-error';
import { DOCUMENTS_PAGE, JOBS_PAGE } from '../../shared/constants/general';

import wizardStyles from 'shared/components/wizard/wizard/wizard.module.scss';
import { Text } from '@epam/loveship';
import { CurrentUser } from 'shared/contexts/current-user';
import { DataSetOptions } from 'shared/components/wizard/dataset-wizard-screen/constants';

export const UploadWizardPage = () => {
    const { isPipelinesDisabled } = useContext(CurrentUser);

    const [stepIndex, setStepIndex] = useState(0);
    const [files, setFiles] = useState<File[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [uploadedFilesIds, setUploadedFilesIds] = useState<number[]>([]);
    const [datasetStepData, setDatasetStepData] = useState<DatasetWizardScreenResult>();
    const [preprocessorStepData, setPreprocessorStepData] =
        useState<UploadWizardPreprocessorResult>();

    const { notifyError, notifySuccess } = useNotifications();
    const uploadFilesMutation = useUploadFilesMutation()();
    const addDatasetMutation = useAddDatasetMutation();
    const addFilesToDatasetMutation = useAddFilesToDatasetMutation();
    const bondFilesToExistingDataset = bondToDataset;

    const history = useHistory();

    const handleJobAdded = (id: number) => {
        if (id) {
            history.push(`${JOBS_PAGE}/${id}`);
        }
    };

    const handleRedirectAfterFinish = () => {
        history.push(DOCUMENTS_PAGE);
    };

    const uploadFilesHandler = useCallback(async () => {
        try {
            setIsLoading(true);
            const responses = await uploadFilesMutation.mutateAsync(files);
            const filesIds: number[] = [];
            for (const response of responses) {
                filesIds.push(response.id);
                notifySuccess(<Text>{response.message}</Text>);
            }
            setUploadedFilesIds(filesIds);
        } catch (error) {
            notifyError(<Text>{getError(error)}</Text>);
        } finally {
            setIsLoading(false);
        }
    }, [files]);

    const isDatasetStepNextDisabled = () =>
        (datasetStepData?.optionId === DataSetOptions.existingDataSet &&
            !datasetStepData.selectedDataset) ||
        (datasetStepData?.optionId === DataSetOptions.newDataSet && !datasetStepData.datasetName);

    const datasetHandler = async () => {
        switch (datasetStepData?.optionId) {
            case DataSetOptions.existingDataSet: {
                const datasetWithFiles: DatasetWithFiles = {
                    name: datasetStepData?.selectedDataset?.name || '',
                    objects: uploadedFilesIds
                };
                await addFilesToDatasetMutation.mutateAsync(datasetWithFiles);
                break;
            }
            case DataSetOptions.newDataSet: {
                // can also be saved to newDataset
                await addDatasetMutation
                    .mutateAsync(datasetStepData.datasetName || '')
                    .finally(() =>
                        bondFilesToExistingDataset(
                            datasetStepData.datasetName || '',
                            uploadedFilesIds
                        )
                    );
                break;
            }
        }
    };

    const preprocessorHandler = async () => {
        if (!preprocessorStepData?.preprocessor || !uploadedFilesIds.length) {
            return;
        }
        await Promise.allSettled([
            runPreprocessing(
                uploadedFilesIds,
                preprocessorStepData?.preprocessor,
                preprocessorStepData?.selectedLanguages
            )
        ]);
    };

    const handleNext = () => {
        setStepIndex(stepIndex + 1);
    };

    const steps: WizardPropsStep[] = [
        {
            title: 'Upload',
            content: (
                <>
                    <div className={wizardStyles['content__body']}>
                        <UploadFilesControl
                            value={files}
                            onValueChange={setFiles}
                            isLoading={isLoading}
                        />
                    </div>
                    <div className={wizardStyles['content__footer']}>
                        {renderWizardButtons({
                            onNextClick: () => {
                                uploadFilesHandler();
                                handleNext();
                            },
                            disableNextButton: !files.length
                        })}
                    </div>
                </>
            )
        },
        {
            title: 'Dataset',
            content: (
                <>
                    <div className={wizardStyles['content__body']}>
                        <DatasetWizardScreen onChange={setDatasetStepData} />
                    </div>
                    <div className={wizardStyles['content__footer']}>
                        {renderWizardButtons({
                            onNextClick: () => {
                                datasetHandler();
                                handleNext();
                            },
                            disableNextButton: isDatasetStepNextDisabled()
                        })}
                    </div>
                </>
            )
        },
        {
            title: 'Preprocessor',
            content: (
                <>
                    <div className={wizardStyles['content__body']}>
                        <UploadWizardPreprocessor onChange={setPreprocessorStepData} />
                    </div>
                    <div className={wizardStyles['content__footer']}>
                        {renderWizardButtons({
                            onNextClick: () => {
                                preprocessorHandler();
                                handleNext();
                            }
                        })}
                    </div>
                </>
            )
        },
        {
            title: 'Extraction and Annotation',
            content: (
                <EditJobConnector
                    onJobAdded={handleJobAdded}
                    onRedirectAfterFinish={handleRedirectAfterFinish}
                    files={uploadedFilesIds}
                    renderWizardButtons={({ save, disableNextButton, finishButtonCaption }) =>
                        renderWizardButtons({
                            onNextClick: save,
                            nextButtonCaption: finishButtonCaption,
                            disableNextButton
                        })
                    }
                    showNoExtractionTab={true}
                />
            )
        }
    ];

    let filteredSteps;
    if (isPipelinesDisabled) filteredSteps = steps.filter((el) => el.title !== 'Preprocessor');
    return (
        <Wizard steps={filteredSteps ?? steps} returnUrl={DOCUMENTS_PAGE} stepIndex={stepIndex} />
    );
};
