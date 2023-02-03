import EditJobConnector from '../../connectors/edit-job-connector/edit-job-connector';
import React, { useEffect, useState } from 'react';
import { Job } from '../../api/typings/jobs';
import { useHistory, useParams } from 'react-router-dom';
import { Button } from '@epam/loveship';
import styles from '../../shared/components/wizard/wizard/wizard.module.scss';
import Wizard, {
    renderWizardButtons,
    WizardPropsStep
} from '../../shared/components/wizard/wizard/wizard';
import { DocumentsTableConnector } from '../../connectors';
import { DOCUMENTS_PAGE } from '../../shared/constants';

import wizardStyles from '../../shared/components/wizard/wizard/wizard.module.scss';
import { useJobById } from 'api/hooks/jobs';

type HistoryState = {
    files?: number[];
    job?: Job;
};

export const EditJobPage = () => {
    const history = useHistory();
    const { jobId } = useParams() as any;

    const [files, setFiles] = useState<number[]>([]);
    const [stepIndex, setStepIndex] = useState(0);

    const { data: job } = useJobById(
        { jobId: Number(jobId) },
        {
            enabled: !!jobId
        }
    );

    useEffect(() => {
        if (!job) return;
        setFiles(job.files);
        console.log(files);
    }, [job]);
    // const historyState = history.location.state as HistoryState;
    // const checkedFiles = historyState?.files;
    // const initialJob = historyState?.job;

    const handleJobAdded = (id: number) => {
        history.push(`${id}`);
    };

    // let startStepId = 0;
    // if (checkedFiles?.length) {
    //     startStepId = 1;
    // }
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
                <EditJobConnector
                    onJobAdded={handleJobAdded}
                    initialJob={job}
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
