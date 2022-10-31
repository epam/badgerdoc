import { ILens } from '@epam/uui';
import { Pipeline } from 'api/typings';
import { JobValues } from 'connectors/add-job-connector/add-job-connector';
import React, { FC } from 'react';
import JobName from '../job-name/job-name';
import PipelinePicker from '../pipeline-picker/pipeline-picker';
import styles from './automatic-job.module.scss';

export type AutomaticJobProps = {
    pipelines: Pipeline[] | undefined;
    lens: ILens<JobValues>;
};
const AutomaticJob: FC<AutomaticJobProps> = ({ pipelines, lens }) => {
    return (
        <div className={styles.job}>
            <JobName lens={lens} />
            <PipelinePicker lens={lens} pipelines={pipelines} />
        </div>
    );
};

export default AutomaticJob;
