import React, { useEffect, useState } from 'react';

import { useHistory, useParams } from 'react-router-dom';
import { Button } from '@epam/loveship';
import Wizard, {
    renderWizardButtons,
    WizardPropsStep
} from '../../shared/components/wizard/wizard/wizard';
import { DocumentsTableConnector } from '../../connectors';
import { JOBS_PAGE } from '../../shared/constants';
import { useJobById } from 'api/hooks/jobs';
import EditJobConnector from '../../connectors/edit-job-connector/edit-job-connector';

import wizardStyles from '../../shared/components/wizard/wizard/wizard.module.scss';
import styles from '../../shared/components/wizard/wizard/wizard.module.scss';

export const EditJobPage = () => {
    const history = useHistory();
    const { jobId } = useParams() as { jobId: string };

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
    }, [job]);

    const handleJobAdded = (id: number) => {
        history.push(`${JOBS_PAGE}/${id}`);
    };

    useEffect(() => {
        if (jobId) {
            setStepIndex(1);
        }
    }, [jobId]);

    const handleNext = () => {
        setStepIndex(stepIndex + 1);
    };
    const handlePrev = () => {
        setStepIndex(stepIndex - 1);
    };

    const finishButtonCaption = jobId ? 'Save Edits' : 'Add Extraction';
    const isDisabled = !!jobId;

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
                                    isDisabled={isDisabled}
                                />
                                <Button
                                    cx={styles.button}
                                    caption="Save as Draft"
                                    isDisabled={isDisabled}
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
    return <Wizard steps={steps} returnUrl={`${JOBS_PAGE}/${jobId}`} stepIndex={stepIndex} />;
};
