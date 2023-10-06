// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare, react-hooks/exhaustive-deps */
import React, { FC, ReactElement, useCallback, useContext, useMemo } from 'react';
import EditJobSettings from 'components/job/edit-job-settings/edit-job-settings';
import { usePipelines } from 'api/hooks/pipelines';
import { JobVariables, useAddJobMutation, useEditJobMutation } from 'api/hooks/jobs';
import {
    Category,
    CategoryRelatedTaxonomies,
    Pipeline,
    SortingDirection,
    Taxonomy,
    User,
    ValidationType
} from 'api/typings';
import { svc } from 'services';
import { getError } from '../../shared/helpers/get-error';
import { useCategories } from 'api/hooks/categories';
import { useUsers } from 'api/hooks/users';
import { JobType, Job } from 'api/typings/jobs';
import { CurrentUser } from 'shared/contexts/current-user';
import wizardStyles from '../../shared/components/wizard/wizard/wizard.module.scss';
import { useAllTaxonomies, useTaxonomiesByJobId } from 'api/hooks/taxons';
import { cloneDeep } from 'lodash';

import { Form, INotification, IFormApi } from '@epam/uui';
import { ErrorNotification, SuccessNotification, Text } from '@epam/loveship';

type EditJobConnectorProps = {
    renderWizardButtons: ({
        save,
        lens,
        disableNextButton,
        finishButtonCaption
    }: {
        save: any;
        lens: any;
        disableNextButton: boolean;
        finishButtonCaption: string;
    }) => ReactElement;
    onJobAdded: (id: number) => void;
    onRedirectAfterFinish?: () => void;
    files: number[];
    checkedFiles?: number[];
    initialJob?: Job;
    showNoExtractionTab?: boolean;
};

export type JobValues = {
    addedJobId?: number;
    jobName: string | undefined;
    pipeline: Pipeline | undefined;
    jobType: JobType | 'NoExtraction';
    deadline: string | undefined;
    categories: Category[] | undefined;
    validationType: ValidationType | undefined;
    owners: User[] | undefined;
    annotators: User[] | undefined;
    validators: User[] | undefined;
    annotators_validators: User[] | undefined;
    is_draft: boolean;
    is_auto_distribution: boolean;
    start_manual_job_automatically: boolean;
    extensive_coverage: number | undefined;
    selected_taxonomies: CategoryRelatedTaxonomies | undefined;
};

const validationTypeTitle = {
    extensive_coverage: 'Extensive Coverage',
    hierarchical: 'Hierarchical Validation'
};
const EditJobConnector: FC<EditJobConnectorProps> = ({
    renderWizardButtons,
    onJobAdded,
    onRedirectAfterFinish,
    files,
    initialJob,
    showNoExtractionTab
}) => {
    const getMetadata = (state: JobValues) => {
        const { jobType, validationType, pipeline, categories } = state;

        const annotatorsValidatorsCombinedFieldRequired = validationType === 'cross' ? true : false;
        const hasLinkTypeCategory = categories?.some((category) => category.type === 'link');
        const hasBoxTypeCategory = categories?.some((category) => category.type === 'box');

        // TODO add proper typing for validators
        const metadata: any = {
            props: {
                jobName: { isRequired: jobType !== 'NoExtraction' },
                pipeline: { isRequired: jobType === 'ExtractionJob' },
                start_manual_job_automatically: { isDisabled: !pipeline },
                validationType: { isRequired: jobType === 'ExtractionWithAnnotationJob' },
                categories: {
                    isRequired: jobType === 'ExtractionWithAnnotationJob'
                },
                extensive_coverage: { isRequired: validationType === 'extensive_coverage' }
            }
        };

        metadata.props['owners'] = {
            validationMessage: 'For Owners at least 1 owner is required',
            isRequired: true
        };

        if (jobType === 'ExtractionWithAnnotationJob') {
            metadata.props['annotators_validators'] = {
                validationMessage:
                    'For Cross validation at least 2 annotators or validators are required',
                isRequired: annotatorsValidatorsCombinedFieldRequired
            };
        }

        if (hasLinkTypeCategory && !hasBoxTypeCategory) {
            const categoriesMetaData = metadata.props['categories'];

            metadata.props['categories'] = {
                ...categoriesMetaData,
                isInvalid: true,
                validationMessage: 'You should select at least one category with type "Box"'
            };
        }

        if (validationType === ValidationType.validationOnly) {
            metadata.props['validators'] = {
                validationMessage: `For Validation only at least 1 validator required`,
                isRequired: true
            };
        }

        if (
            validationType === ValidationType.extensiveCoverage ||
            validationType === ValidationType.hierarchical
        ) {
            metadata.props['annotators'] = {
                validationMessage: `For ${validationTypeTitle[validationType]} at least 1 annotator required`,
                isRequired: true
            };
            metadata.props['validators'] = {
                validationMessage: `For ${validationTypeTitle[validationType]} at least 1 validator required`,
                isRequired: true
            };
        }

        return metadata;
    };

    const { pipelines, categories, users, taxonomies } = useEntities();

    const addJobMutation = useAddJobMutation();
    const editJobMutation = useEditJobMutation();

    const renderForm = useCallback(
        ({ lens, save }: IFormApi<JobValues>) => {
            const values = lens.get();
            const isInvalidCategoryList = lens.prop('categories').toProps().isInvalid;

            let isValid;
            switch (values.jobType) {
                case 'NoExtraction':
                    isValid = true;
                    break;
                case 'ExtractionJob':
                    isValid = !!values.jobName && !!values.pipeline;
                    break;
                case 'ExtractionWithAnnotationJob':
                    isValid = !!values.jobName;
                    break;
            }

            const onSubmit = () => {
                if (!isInvalidCategoryList) {
                    return save;
                }

                return () => {};
            };

            return (
                <>
                    <div className={wizardStyles['content__body']}>
                        <EditJobSettings
                            initialType={initialJob?.type}
                            pipelines={pipelines}
                            users={users}
                            taxonomies={taxonomies}
                            lens={lens}
                            showNoExtractionTab={showNoExtractionTab}
                        />
                    </div>
                    <div className={wizardStyles['content__footer']}>
                        {renderWizardButtons({
                            save: onSubmit(),
                            lens,
                            disableNextButton: !isValid,
                            finishButtonCaption:
                                values.jobType === 'NoExtraction' ? 'Finish' : 'Start Extraction'
                        })}
                    </div>
                </>
            );
        },
        [pipelines, categories, users, taxonomies]
    );

    const handleSave = useCallback(
        async (values: JobValues) => {
            const {
                jobName,
                jobType,
                deadline: jobDeadline,
                categories = [],
                validationType,
                owners = [],
                annotators: jobAnnotator = [],
                validators: jobValidators = [],
                annotators_validators = [],
                is_draft,
                is_auto_distribution,
                start_manual_job_automatically,
                extensive_coverage,
                selected_taxonomies,
                pipeline
            } = values;

            if (jobType === 'NoExtraction') {
                onRedirectAfterFinish?.();
                return;
            }

            const deadline = jobDeadline ? new Date(jobDeadline).toISOString() : undefined;
            const annotators = validationType === 'cross' ? annotators_validators : jobAnnotator;
            const validators = validationType === 'cross' ? [] : jobValidators;

            const jobProps: JobVariables = {
                name: jobName,
                files,
                datasets: [],
                type:
                    jobType === 'ExtractionJob'
                        ? 'ExtractionJob'
                        : pipeline
                        ? 'ExtractionWithAnnotationJob'
                        : 'AnnotationJob',
                is_draft,
                is_auto_distribution: jobType !== 'ExtractionJob' && is_auto_distribution,
                start_manual_job_automatically:
                    jobType !== 'ExtractionJob' && start_manual_job_automatically,
                extensive_coverage,
                categories: categories.map((category) => category.id),
                deadline,
                validation_type: validationType,
                owners: owners.map((owner) => owner.id),
                annotators: annotators.map((annotator) => annotator.id),
                validators: validators.map((validator) => validator.id),
                pipeline_name: pipeline?.name,
                pipeline_version: pipeline?.version
            };

            if (!pipeline) {
                delete jobProps.start_manual_job_automatically;
            }

            if (selected_taxonomies) {
                jobProps.categories = jobProps.categories?.map((categoryId) => {
                    const currentTaxonomy = selected_taxonomies[categoryId as string | number];
                    if (currentTaxonomy) {
                        return {
                            category_id: categoryId?.toString(),
                            taxonomy_id: currentTaxonomy.id,
                            taxonomy_version: currentTaxonomy.version!
                        };
                    }
                    return categoryId;
                });
            }

            try {
                if (initialJob?.id) {
                    const editData = cloneDeep(jobProps);
                    delete editData.files;
                    delete editData.datasets;
                    await editJobMutation.mutateAsync({
                        id: initialJob.id,
                        data: editData
                    });
                    return { form: values };
                }

                const response = await addJobMutation.mutateAsync(jobProps);
                values.addedJobId = response.id;
                return { form: values };
            } catch (err: any) {
                svc.uuiNotifications.show(
                    (props: INotification) => (
                        <ErrorNotification {...props}>
                            <Text>{getError(err)}</Text>
                        </ErrorNotification>
                    ),
                    { duration: 2 }
                );
                return {
                    form: values,
                    validation: {
                        isInvalid: true
                    }
                };
            }
        },
        [files, addJobMutation, editJobMutation, initialJob, onRedirectAfterFinish]
    );

    const handleSuccess = useCallback(
        ({ addedJobId }: JobValues) => {
            svc.uuiNotifications.show(
                (props: INotification) => (
                    <SuccessNotification {...props}>
                        <Text>Extraction created successfully!</Text>
                    </SuccessNotification>
                ),
                { duration: 2 }
            );
            if (addedJobId) {
                onJobAdded(addedJobId);
            }
        },
        [onJobAdded]
    );

    const formValues = useEditJobFormValues({
        initialJob,
        pipelines,
        categories,
        users,
        taxonomies
    });

    if (!formValues) {
        return null;
    }

    return (
        <Form<JobValues>
            renderForm={renderForm}
            onSave={handleSave}
            value={formValues}
            getMetadata={getMetadata}
            onSuccess={handleSuccess}
        />
    );
};

export default EditJobConnector;

const useEntities = () => {
    const pipelinesResult = usePipelines(
        {
            page: 1,
            size: 100,
            searchText: '',
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        {}
    );

    const categoriesResult = useCategories(
        {
            page: 1,
            size: 100,
            searchText: '',
            sortConfig: { field: 'name', direction: SortingDirection.ASC }
        },
        {}
    );

    const usersResult = useUsers(
        {
            page: 1,
            size: 100,
            searchText: '',
            sortConfig: { field: 'username', direction: SortingDirection.ASC }
        },
        {}
    );

    const taxonomiesResult = useAllTaxonomies({
        page: 1,
        size: 100,
        searchText: '',
        sortConfig: { field: 'name', direction: SortingDirection.ASC }
    });

    return {
        pipelines: pipelinesResult.data?.data,
        categories: categoriesResult.data?.data,
        users: usersResult.data?.data,
        taxonomies: taxonomiesResult.data?.data
    };
};

interface Params {
    initialJob?: Job;
    pipelines?: Pipeline[];
    categories?: Category[];
    users?: User[];
    taxonomies?: Taxonomy[];
}

const useEditJobFormValues = ({
    initialJob,
    pipelines,
    categories,
    users,
    taxonomies
}: Params): JobValues | null => {
    const { currentUser, isPipelinesDisabled } = useContext(CurrentUser);

    const initialValues: JobValues = {
        jobName: undefined,
        pipeline: undefined,
        jobType: isPipelinesDisabled ? 'ExtractionWithAnnotationJob' : 'ExtractionJob',
        deadline: undefined,
        categories: undefined,
        validationType: undefined,
        owners: undefined,
        annotators: undefined,
        validators: undefined,
        annotators_validators: undefined,
        is_draft: false,
        is_auto_distribution: true,
        start_manual_job_automatically: true,
        extensive_coverage: undefined,
        selected_taxonomies: undefined
    };

    const { data: categoriesAndTaxonomies } = useTaxonomiesByJobId(
        { jobId: initialJob?.id },
        { enabled: !!initialJob }
    );

    let selectedTaxonomies: CategoryRelatedTaxonomies | undefined = useMemo(() => {
        if (!categoriesAndTaxonomies) return;
        const entries = categoriesAndTaxonomies.map((catAndTax) => [
            catAndTax.category_id,
            {
                id: catAndTax.id,
                name: catAndTax.name,
                version: catAndTax.version
            }
        ]);
        return Object.fromEntries(entries);
    }, [categoriesAndTaxonomies]);

    return useMemo(() => {
        if (!initialJob) {
            return {
                ...initialValues,
                owners: [currentUser!]
            };
        }

        if (!pipelines || !categories || !users) {
            return null;
        }

        return {
            ...initialValues,
            addedJobId: initialJob.id,
            jobName: initialJob.name,
            jobType: initialJob.type,
            deadline: initialJob.deadline,
            validationType: initialJob.validation_type,
            annotators:
                initialJob.validation_type !== 'cross'
                    ? initialJob.annotators?.map((annotator) => {
                          const user = users?.find((user) => user.id === annotator.id);
                          if (user) return user;
                          return {} as User;
                      })
                    : [],
            validators:
                initialJob.validators?.map((el) => {
                    const user = users?.find((user) => user.id === el);
                    if (user) return user;
                    return {} as User;
                }) || [],
            annotators_validators:
                initialJob.validation_type === 'cross'
                    ? initialJob.annotators?.map((annotator) => {
                          const user = users?.find((user) => user.id === annotator.id);
                          if (user) return user;
                          return {} as User;
                      })
                    : [],
            owners:
                initialJob.owners?.map((el) => {
                    const user = users?.find((user) => user.id === el);
                    if (user) return user;
                    return {} as User;
                }) || [],
            pipeline: pipelines?.find((el) => el.id === parseInt(initialJob.pipeline_id)),
            categories:
                initialJob.categories
                    ?.map((el) => {
                        const category = categories?.find((elem) => elem.id === el.toString());
                        return category as Category;
                    })
                    .filter(Boolean) || [],
            selected_taxonomies: selectedTaxonomies,
            extensive_coverage: initialJob.extensive_coverage
        };
    }, [currentUser, initialJob, pipelines, categories, users, taxonomies, selectedTaxonomies]);
};
