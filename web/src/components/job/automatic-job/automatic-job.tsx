// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC, useContext } from 'react';
import { PipelineManager } from 'api/typings';
import { JobValues } from 'connectors/edit-job-connector/edit-job-connector';
import JobName from '../job-name/job-name';
import PipelinePicker from '../pipeline-picker/pipeline-picker';

import { ILens } from '@epam/uui';
import styles from './automatic-job.module.scss';
import { CurrentUser } from 'shared/contexts/current-user';

export type AutomaticJobProps = {
    pipelineManagers?: PipelineManager[];
    lens: ILens<JobValues>;
};
const AutomaticJob: FC<AutomaticJobProps> = ({ pipelineManagers, lens }) => {
    const { isPipelinesDisabled } = useContext(CurrentUser);
    return (
        <div className={styles.job}>
            <JobName lens={lens} />
            {!isPipelinesDisabled && (
                <PipelinePicker lens={lens} pipelineManagers={pipelineManagers} />
            )}
        </div>
    );
};

export default AutomaticJob;
