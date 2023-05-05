import React, { FC, useState } from 'react';
import { useArrayDataSource } from '@epam/uui';
import { PickerInput, Button, ControlGroup, Tooltip } from '@epam/loveship';

import { ReactComponent as settingsIcon } from '@epam/assets/icons/common/navigation-more_vert-18.svg';
import styles from './finish-button.module.scss';
import { ValidationType } from '../../../../api/typings';
import { TaskStatus } from '../../../../api/typings/tasks';
import { createTooltip } from './utils';

type TaskSidebarProps = {
    viewMode: boolean;
    isValidation: boolean;
    allValidated: boolean;
    isAnnotatable: boolean;
    isSplitValidation: boolean;
    isNextTaskPresented?: boolean;
    editedPagesCount: number;
    touchedPagesCount: number;
    notProcessedPages: number[];
    onFinishValidation: () => void;
    onAnnotationTaskFinish: () => void;
    onFinishSplitValidation: () => void;
    onSaveTask: () => void;
    jobType?: ValidationType;
    taskStatus?: TaskStatus;
};

export const FinishButton: FC<TaskSidebarProps> = ({
    viewMode,
    isValidation,
    allValidated,
    isAnnotatable,
    editedPagesCount,
    isSplitValidation,
    touchedPagesCount,
    notProcessedPages,
    isNextTaskPresented,
    onFinishValidation,
    onAnnotationTaskFinish,
    onFinishSplitValidation,
    jobType
}) => {
    const [redirectionSettings, setRedirectionSettings] = useState(
        localStorage.getItem('submitted-task-redirection-page') ?? 'tasks'
    );

    const handleSetRedirectionSettings = (value: 'tasks' | 'next-task') => {
        setRedirectionSettings(value);
        localStorage.setItem('submitted-task-redirection-page', value);
    };

    const handleFinishValidation = isSplitValidation ? onFinishSplitValidation : onFinishValidation;

    let isDisabled = !isAnnotatable;
    if (jobType !== 'extensive_coverage') {
        isDisabled =
            !isAnnotatable ||
            !allValidated ||
            (isValidation && !touchedPagesCount && !editedPagesCount);
    }

    const tooltipContent =
        isDisabled && allValidated && !isSplitValidation
            ? ''
            : createTooltip(jobType === 'extensive_coverage', notProcessedPages);

    const redirectSettingsDataSource = useArrayDataSource(
        {
            items: [
                { id: 'tasks', caption: 'Redirect to the Tasks page after submit' },
                { id: 'next-task', caption: 'Redirect to the next Task after submit' }
            ]
        },
        []
    );

    return !isValidation && viewMode ? null : (
        <ControlGroup cx={styles['button-finish-control-group']}>
            <Tooltip content={tooltipContent}>
                <Button
                    isDisabled={isDisabled}
                    cx={styles['button-finish']}
                    caption={isValidation ? 'FINISH VALIDATION' : 'FINISH LABELING'}
                    onClick={
                        isValidation
                            ? () => {
                                  handleFinishValidation();
                              }
                            : onAnnotationTaskFinish
                    }
                />
            </Tooltip>
            {isNextTaskPresented && (
                <PickerInput
                    valueType="id"
                    minBodyWidth={322}
                    selectionMode="single"
                    value={redirectionSettings}
                    dataSource={redirectSettingsDataSource}
                    getName={(item) => item?.caption ?? ''}
                    onValueChange={handleSetRedirectionSettings}
                    renderToggler={({ toggleDropdownOpening, ...props }) => (
                        <Button
                            {...props}
                            size="36"
                            fill="solid"
                            isDropdown={false}
                            icon={settingsIcon}
                            onClear={undefined}
                            placeholder={undefined}
                            isDisabled={isDisabled}
                            onClick={toggleDropdownOpening}
                        />
                    )}
                />
            )}
        </ControlGroup>
    );
};
