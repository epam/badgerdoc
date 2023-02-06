import { ILens } from '@epam/uui';
import { Category, Pipeline, Taxonomy, User } from 'api/typings';
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
import { ExtensiveCoverageInput } from './extensive-coverage-input/extensive-coverage-input';
import TaxonomyPickers from 'shared/components/taxonomy-pickers/taxonomy-pickers';

type AutomaticManualJobProps = {
    categories: Category[] | undefined;
    users: User[] | undefined;
    pipelines: Pipeline[] | undefined;
    taxonomies: Taxonomy[] | undefined;
    lens: ILens<JobValues>;
};
const AutomaticManualJob: FC<AutomaticManualJobProps> = ({
    lens,
    categories,
    users,
    taxonomies,
    pipelines
}) => {
    const startManuallyProps = lens.prop('start_manual_job_automatically').toProps();
    if (startManuallyProps.isDisabled) {
        startManuallyProps.value = false;
    }

    const categoriesWithTaxonomy = lens
        .prop('categories')
        .get()
        ?.filter((category) => (category.data_attributes || [])[0]?.type === 'taxonomy');

    const validationType = lens.prop('validationType').get();
    return (
        <div className={styles.job}>
            <JobName lens={lens} />
            {process.env.REACT_APP_CONF !== 'myConf' && (
                <PipelinePicker lens={lens} pipelines={pipelines} />
            )}
            <div className="flex">
                <ValidationTypePicker lens={lens} />
                <DeadlinePicker lens={lens} />
            </div>
            <UsersPickers lens={lens} users={users} />
            {validationType === 'extensive_coverage' && <ExtensiveCoverageInput lens={lens} />}

            <div className="form-group">
                <CategoriesPicker lens={lens} categories={categories} />
            </div>
            <div className="form-group">
                <TaxonomyPickers
                    lens={lens}
                    taxonomies={taxonomies}
                    categories={categoriesWithTaxonomy}
                />
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
