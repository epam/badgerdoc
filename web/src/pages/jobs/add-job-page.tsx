import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { Job } from '../../api/typings/jobs';
import Wizard, {
    renderWizardButtons,
    WizardPropsStep
} from '../../shared/components/wizard/wizard/wizard';
import { DocumentsTableConnector } from '../../connectors';
import AddJobConnector from '../../connectors/add-job-connector/add-job-connector';
import { DOCUMENTS_PAGE } from '../../shared/constants';

import { Button } from '@epam/loveship';
import styles from '../../shared/components/wizard/wizard/wizard.module.scss';
import wizardStyles from '../../shared/components/wizard/wizard/wizard.module.scss';

type HistoryState = {
    files?: number[];
    job?: Job;
};

export const AddJobPage = () => {
    const history = useHistory();
    const historyState = history.location.state as HistoryState;
    const checkedFiles = historyState?.files;
    const initialJob = historyState?.job;

    const handleJobAdded = (id: number) => {
        history.push(`${id}`);
    };

    const [files, setFiles] = useState<number[]>(checkedFiles || initialJob?.files || []);

    let startStepId = 0;
    if (checkedFiles?.length) {
        startStepId = 1;
    }
    const [stepIndex, setStepIndex] = useState(startStepId);
    const handleNext = () => {
        setStepIndex(stepIndex + 1);
    };
    const handlePrev = () => {
        setStepIndex(stepIndex - 1);
    };
    const finishButtonCaption = 'Add Extraction';

    const steps: WizardPropsStep[] = [
        {
            title: 'Datasets',
            content: (
                <>
                    <div className={wizardStyles['content__body']}>
                        <div className="form-wrapper">
                            <DocumentsTableConnector
                                isJobPage
                                onFilesSelect={setFiles}
                                onRowClick={() => null}
                                checkedValues={files}
                            />
                        </div>
                    </div>
                    <div className={wizardStyles['content__footer']}>
                        {renderWizardButtons({
                            onNextClick: handleNext
                        })}
                    </div>
                </>
            )
        },
        {
            title: 'Settings',
            content: (
                <AddJobConnector
                    onJobAdded={handleJobAdded}
                    initialJob={historyState?.job}
                    files={files}
                    renderWizardButtons={({ save, lens }) => {
                        return (
                            <>
                                <Button
                                    fill="light"
                                    cx={styles.button}
                                    caption="Previous"
                                    onClick={handlePrev}
                                />
                                <Button
                                    cx={styles.button}
                                    caption="Save as Draft"
                                    fill="none"
                                    onClick={() => {
                                        lens.prop('is_draft').set(true);
                                        save();
                                    }}
                                />
                                <Button
                                    cx={styles.button}
                                    caption={finishButtonCaption}
                                    onClick={save}
                                />
                            </>
                        );
                    }}
                />
            )
        }
    ];
    return <Wizard steps={steps} returnUrl={DOCUMENTS_PAGE} stepIndex={stepIndex} />;
};
