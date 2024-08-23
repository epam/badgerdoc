// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useEffect, useState } from 'react';

import { useHistory, useParams } from 'react-router-dom';
import { Button, MultiSwitch } from '@epam/loveship';
import Wizard, {
    renderWizardButtons,
    WizardPropsStep
} from '../../shared/components/wizard/wizard/wizard';
import { DocumentsTableConnector } from '../../connectors';
import { JobsTableConnector } from '../../connectors';
import { JOBS_PAGE } from '../../shared/constants/general';
import { useJobById } from 'api/hooks/jobs';
import EditJobConnector from '../../connectors/edit-job-connector/edit-job-connector';
import { DatasetsTableConnector } from 'connectors/datasets-table-connector';

import wizardStyles from '../../shared/components/wizard/wizard/wizard.module.scss';
import styles from '../../shared/components/wizard/wizard/wizard.module.scss';
import pageStyles from './edit-job-page.module.scss';

export const EditJobPage = () => {
    const history = useHistory();
    const { jobId } = useParams() as { jobId: string };

    const [files, setFiles] = useState<number[]>([]);
    const [jobs, setJobs] = useState<number[]>([]);
    const [datasets, setDatasets] = useState<number[]>([]);
    const [stepIndex, setStepIndex] = useState(0);
    const [currentTab, onCurrentTabChange] = useState('Documents');

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

    const finishButtonCaption = jobId ? 'Save Edits' : 'New Job';
    const isDisabled = !!jobId;

    const tabs = [
        {
            id: 'Documents',
            caption: 'Documents'
        },
        {
            id: 'Jobs',
            caption: 'Jobs'
        },
        {
            id: 'Datasets',
            caption: 'Datasets'
        }
    ];

    let table;

    if (currentTab === 'Documents') {
        table = (
            <DocumentsTableConnector
                isJobPage
                onFilesSelect={setFiles}
                onRowClick={() => null}
                checkedValues={files}
            />
        );
    } else if (currentTab === 'Jobs') {
        table = (
            <JobsTableConnector
                isNewJobPage
                onJobsSelect={setJobs}
                onRowClick={() => null}
                onAddJob={() => null}
                checkedValues={jobs}
            />
        );
    } else {
        table = (
            <DatasetsTableConnector
                onDatasetSelect={setDatasets}
                onRowClick={() => null}
                checkedValues={datasets}
            />
        );
    }

    const steps: WizardPropsStep[] = [
        {
            title: 'Datasets',
            content: (
                <>
                    <div className={wizardStyles['content__body']}>
                        <div className={`${pageStyles.container} flex flex-col`}>
                            <div className={pageStyles.tabs}>
                                <MultiSwitch
                                    size="42"
                                    items={tabs}
                                    onValueChange={onCurrentTabChange}
                                    value={currentTab}
                                />
                            </div>
                            <div className={`form-wrapper`}>{table}</div>
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
                    files={currentTab === 'Documents' ? files : []}
                    jobs={currentTab === 'Jobs' ? jobs : []}
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
