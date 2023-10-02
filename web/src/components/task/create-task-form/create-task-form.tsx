// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import React, { FC, ReactNode, useCallback, useRef, useState } from 'react';
import DatePicker from 'react-datepicker';
import {
    Button,
    FlexRow,
    FlexSpacer,
    Form,
    LabeledInput,
    ModalFooter,
    ModalHeader,
    Panel,
    PickerInput,
    Switch,
    TextInput
} from '@epam/loveship';
import { TaskModel } from 'api/typings/tasks';
import { ILens, LazyDataSource, Metadata, IFormApi } from '@epam/uui';
import { FileDocument, User } from 'api/typings';

import 'react-datepicker/src/stylesheets/datepicker.scss';
import styles from './create-task-form.module.scss';

type FormTaskModel = Partial<
    Pick<TaskModel, 'file_id' | 'user_id' | 'pages' | 'is_validation' | 'deadline'>
>;

type CreateTaskFormProps = {
    onTaskCreation(task: TaskModel): Promise<void>;
    onSuccess(task: FormTaskModel): void;
    filesDataSource: LazyDataSource<FileDocument, number>;
    annotatorsDataSource: LazyDataSource<User, string>;
    onCancelButton(): void;
};

export const CreateTaskForm: FC<CreateTaskFormProps> = ({
    onTaskCreation,
    onSuccess,
    filesDataSource,
    annotatorsDataSource,
    onCancelButton
}) => {
    const task = useRef<FormTaskModel>({
        pages: [],
        is_validation: false
    });
    const [pageInputValue, setPageInputValue] = useState<string>();
    const [deadlineDate, setDeadlineDate] = useState<Date | null>(null);

    const onPageInput = useCallback(
        (input: string, lens: ILens<FormTaskModel>) => {
            lens.prop('pages').set(input.split(',') as unknown[] as number[]);
            setPageInputValue(input);
        },
        [pageInputValue]
    );

    const onDeadlineChange = useCallback(
        (value: Date, lens: ILens<FormTaskModel>) => {
            setDeadlineDate(value);
            if (value) {
                const date = `${value.getFullYear()}-${value.getMonth() + 1}-${value.getDate()}`;
                const time = `${value.getHours()}:${value.getMinutes()}:${value.getSeconds()}`;
                lens.prop('deadline').set(`${date} ${time}`);
            } else {
                lens.prop('deadline').set('');
            }
        },
        [setDeadlineDate]
    );

    const renderForm = ({ lens, save }: IFormApi<FormTaskModel>): ReactNode => {
        return (
            <>
                <FlexRow>
                    <ModalHeader title="Create task"></ModalHeader>
                    <Switch label="Is Validation Task" {...lens.prop('is_validation').toProps()} />
                </FlexRow>
                <Panel>
                    <FlexRow padding="24" vPadding="12">
                        <LabeledInput label="File" {...lens.prop('file_id').toProps()}>
                            <PickerInput<FileDocument, number>
                                {...lens.prop('file_id').toProps()}
                                selectionMode="single"
                                valueType="id"
                                getName={(file) => file.original_name}
                                dataSource={filesDataSource}
                                searchPosition="body"
                            />
                        </LabeledInput>
                    </FlexRow>
                    <FlexRow padding="24" vPadding="12">
                        <LabeledInput label="Annotators" {...lens.prop('user_id').toProps()}>
                            <PickerInput<User, string>
                                {...lens.prop('user_id').toProps()}
                                selectionMode="single"
                                valueType="id"
                                getName={(user) => user.username}
                                dataSource={annotatorsDataSource}
                                searchPosition="body"
                            />
                        </LabeledInput>
                    </FlexRow>
                    <FlexRow padding="24" vPadding="12">
                        <FlexRow cx="flex-cell-important justify-between">
                            <LabeledInput
                                cx="flex-cell"
                                label="Pages"
                                {...lens.prop('pages').toProps()}
                            >
                                <TextInput
                                    {...lens.prop('pages').toProps()}
                                    value={pageInputValue}
                                    onValueChange={(value = '') => onPageInput(value, lens)}
                                    placeholder="Pages separated by comma"
                                />
                            </LabeledInput>
                            <LabeledInput
                                label="Deadline"
                                {...lens.prop('deadline').toProps()}
                                cx={styles['date-picker-label']}
                            >
                                <DatePicker
                                    className={`${styles['date-picker']} ${
                                        styles[
                                            lens.prop('deadline').toProps().isInvalid
                                                ? 'date-picker-invalid'
                                                : 'date-picker'
                                        ]
                                    }`}
                                    selected={deadlineDate}
                                    onChange={(date) => onDeadlineChange(date as Date, lens)}
                                    timeInputLabel="Time:"
                                    dateFormat="MM/dd/yyyy h:mm aa"
                                    shouldCloseOnSelect={false}
                                    showTimeInput
                                />
                            </LabeledInput>
                        </FlexRow>
                    </FlexRow>
                </Panel>
                <ModalFooter>
                    <FlexSpacer />
                    <Button fill="white" onClick={onCancelButton} caption="Cancel" />
                    <Button color="sky" caption="Save" onClick={save} />
                </ModalFooter>
            </>
        );
    };

    const getMetaData = (): Metadata<FormTaskModel> => ({
        props: {
            file_id: {
                isRequired: true
            },
            user_id: {
                isRequired: true
            },
            pages: {
                isRequired: true,
                validators: [
                    (value) => {
                        if (!/^[0-9]+(,[0-9]+)*$/.test((value ?? []).join(','))) {
                            return ['Wrong format'];
                        }
                        return [false];
                    }
                ]
            },
            deadline: {
                isRequired: true
            }
        }
    });

    return (
        <Form<FormTaskModel>
            beforeLeave={null}
            value={task.current}
            onSave={onTaskCreation}
            onSuccess={onSuccess}
            renderForm={renderForm}
            getMetadata={getMetaData}
        />
    );
};
