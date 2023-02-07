import React, { FC } from 'react';
import { Pipeline } from 'api/typings';
import { JobValues } from 'connectors/add-job-connector/add-job-connector';
import JobName from '../job-name/job-name';
import PipelinePicker from '../pipeline-picker/pipeline-picker';

import { ILens } from '@epam/uui';
import styles from './automatic-job.module.scss';

export type AutomaticJobProps = {
    pipelines: Pipeline[] | undefined;
    lens: ILens<JobValues>;
};
const AutomaticJob: FC<AutomaticJobProps> = ({ pipelines, lens }) => {
    return (
        <div className={styles.job}>
            <JobName lens={lens} />
            {process.env.REACT_APP_CONF !== 'trm_env' && (
                <PipelinePicker lens={lens} pipelines={pipelines} />
            )}
        </div>
    );
};

export default AutomaticJob;
