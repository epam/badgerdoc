import React, { FC, ReactElement, useCallback, useContext, useMemo } from 'react';
import AddJobSettings from 'components/job/add-job-settings/add-job-settings';
import { usePipelines } from 'api/hooks/pipelines';
import { JobVariables, useAddJobMutation } from 'api/hooks/jobs';
import { Category, Pipeline, SortingDirection, User, ValidationType } from 'api/typings';
import { Form, INotification, RenderFormProps } from '@epam/uui';
import { ErrorNotification, SuccessNotification, Text } from '@epam/loveship';
import { svc } from 'services';
import { getError } from '../../shared/helpers/get-error';
import { useCategories } from 'api/hooks/categories';
import { useUsers } from 'api/hooks/users';
import { Job, JobType } from 'api/typings/jobs';
import { CurrentUser } from 'shared/contexts/current-user';
import wizardStyles from '../../shared/components/wizard/wizard/wizard.module.scss';

type AddJobConnectorProps = {
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
};

const AddJobConnector: FC<AddJobConnectorProps> = ({
    renderWizardButtons,
    onJobAdded,
    files,
    initialJob,
    showNoExtractionTab
}) => {
    const getMetadata = (state: JobValues) => ({
        props: {
            jobName: { isRequired: true },
            pipeline: { isRequired: state.jobType === 'ExtractionJob' },
            start_manual_job_automatically: { isDisabled: !state.pipeline }
        }
    });

    const { pipelines, categories, users } = useEntities();

    const addJobMutation = useAddJobMutation();

    const renderForm = useCallback(
        ({ lens, save }: RenderFormProps<JobValues>) => {
            const values = lens.get();

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

            return (
                <>
                    <div className={wizardStyles['content__body']}>
                        <AddJobSettings
                            initialType={initialJob?.type}
                            pipelines={pipelines}
                            categories={categories}
                            users={users}
                            lens={lens}
                            showNoExtractionTab={showNoExtractionTab}
                        />
                    </div>
                    <div className={wizardStyles['content__footer']}>
                        {renderWizardButtons({
                            save,
                            lens,
                            disableNextButton: !isValid,
                            finishButtonCaption:
                                values.jobType === 'NoExtraction' ? 'Finish' : 'Start Extraction'
                        })}
                    </div>
                </>
            );
        },
        [pipelines, categories, users]
    );

    const handleSave = useCallback(
        async (values: JobValues) => {
            if (values.jobType === 'NoExtraction') {
                return;
            }

            const jobProps: JobVariables = {
                name: values.jobName,
                files,
                datasets: [],
                type:
                    values.jobType === 'ExtractionJob'
                        ? 'ExtractionJob'
                        : values.pipeline
                        ? 'ExtractionWithAnnotationJob'
                        : 'AnnotationJob',
                is_draft: values.is_draft,
                is_auto_distribution: values.is_auto_distribution,
                start_manual_job_automatically: values.start_manual_job_automatically
            };

            const deadline = values.deadline
                ? new Date(values.deadline).toISOString()
                : values.deadline;

            const annotators =
                values.validationType === 'cross'
                    ? values.annotators_validators
                    : values.annotators;
            const validators = values.validationType === 'cross' ? [] : values.validators;
            jobProps.pipeline_name = values.pipeline?.name;
            jobProps.pipeline_version = values.pipeline?.version;
            if (values.jobType === 'ExtractionJob') {
                jobProps.is_auto_distribution = false;
                jobProps.start_manual_job_automatically = false;
            } else if (values.jobType === 'ExtractionWithAnnotationJob') {
                jobProps.categories = values?.categories?.map((category) => category.id);
                jobProps.deadline = deadline;
                jobProps.validation_type = values.validationType;
                jobProps.owners = values.owners?.map((owner) => owner.id);
                jobProps.annotators = annotators?.map((annotator) => annotator.id) ?? [];
                jobProps.validators = validators?.map((validator) => validator.id);
            }
            if (!values.pipeline) {
                delete jobProps.start_manual_job_automatically;
            }
            try {
                const response = await addJobMutation.mutateAsync(jobProps);
                values.addedJobId = response.id;
                return {
                    form: values
                };
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
        [files]
    );

    const handleSuccess = useCallback(
        (values: JobValues) => {
            svc.uuiNotifications.show(
                (props: INotification) => (
                    <SuccessNotification {...props}>
                        <Text>Extraction created successfully!</Text>
                    </SuccessNotification>
                ),
                { duration: 2 }
            );
            if (values.addedJobId) {
                onJobAdded(values.addedJobId);
            }
        },
        [onJobAdded]
    );

    const formValues = useAddJobFormValues({ initialJob, pipelines, categories, users });

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

export default AddJobConnector;

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

    return {
        pipelines: pipelinesResult.data?.data,
        categories: categoriesResult.data?.data,
        users: usersResult.data?.data
    };
};

let initialValues: JobValues = {
    jobName: undefined,
    pipeline: undefined,
    jobType: 'ExtractionJob',
    deadline: undefined,
    categories: undefined,
    validationType: undefined,
    owners: undefined,
    annotators: undefined,
    validators: undefined,
    annotators_validators: undefined,
    is_draft: false,
    is_auto_distribution: true,
    start_manual_job_automatically: true
};

interface Params {
    initialJob?: Job;
    pipelines?: Pipeline[];
    categories?: Category[];
    users?: User[];
}

const useAddJobFormValues = ({
    initialJob,
    pipelines,
    categories,
    users
}: Params): JobValues | null => {
    const { currentUser } = useContext(CurrentUser);

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
                initialJob.annotators?.map((el) => {
                    const user = users?.find((elem) => elem.id === el);
                    if (user) return user;
                    return {} as User;
                }) || [],
            validators:
                initialJob.validators?.map((el) => {
                    const user = users?.find((elem) => elem.id === el);
                    if (user) return user;
                    return {} as User;
                }) || [],
            owners:
                initialJob.owners?.map((el) => {
                    const user = users?.find((elem) => elem.id === el);
                    if (user) return user;
                    return {} as User;
                }) || [],
            pipeline: pipelines?.find((el) => el.id === parseInt(initialJob.pipeline_id)),
            categories:
                initialJob.categories?.map((el) => {
                    const category = categories?.find((elem) => elem.id === el.toString());
                    if (category) return category;
                    return {} as Category;
                }) || []
        };
    }, [currentUser, initialJob, pipelines, categories, users]);
};
