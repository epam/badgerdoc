import { ILens } from '@epam/uui';
import { Category, Pipeline, User } from 'api/typings';
import { JobValues } from 'connectors/add-job-connector/add-job-connector';
import React, { FC } from 'react';
import JobName from '../job-name/job-name';
import styles from './automatic-manual-job.module.scss';
import ValidationTypePicker from '../validation-type-picker/validation-type-picker';
import DeadlinePicker from '../deadline-picker/deadline-picker';
import UsersPickers from '../users-pickers/users-pickers';
import PipelinePicker from '../pipeline-picker/pipeline-picker';
import CategoriesPicker from 'shared/components/categories-picker/categories-picker';
import { Checkbox } from '@epam/loveship';

type AutomaticManualJobProps = {
    categories: Category[] | undefined;
    users: User[] | undefined;
    pipelines: Pipeline[] | undefined;
    lens: ILens<JobValues>;
};
const AutomaticManualJob: FC<AutomaticManualJobProps> = ({
    lens,
    categories,
    users,
    pipelines
}) => {
    const startManuallyProps = lens.prop('start_manual_job_automatically').toProps();
    if (startManuallyProps.isDisabled) {
        startManuallyProps.value = false;
    }

    return (
        <div className={styles.job}>
            <JobName lens={lens} />
            <PipelinePicker lens={lens} pipelines={pipelines} />
            <div className="flex">
                <ValidationTypePicker lens={lens} />
                <DeadlinePicker lens={lens} />
            </div>
            <UsersPickers lens={lens} users={users} />
            <div className="form-group">
                <CategoriesPicker lens={lens} categories={categories} />
            </div>
            <div className="form-group">
                <Checkbox
                    label={'Distribute annotation tasks automatically'}
                    {...lens.prop('is_auto_distribution').toProps()}
                />
            </div>
            <div className="form-group">
                <Checkbox
                    label={'Start manual extraction job automatically'}
                    {...startManuallyProps}
                />
            </div>
        </div>
    );
};

export default AutomaticManualJob;
