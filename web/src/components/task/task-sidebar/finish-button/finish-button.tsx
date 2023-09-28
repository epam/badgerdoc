// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC, useState } from 'react';
import { useArrayDataSource } from '@epam/uui';
import { PickerInput, Button, ControlGroup, Tooltip } from '@epam/loveship';

import { ReactComponent as settingsIcon } from '@epam/assets/icons/common/navigation-more_vert-18.svg';
import styles from './finish-button.module.scss';
import { ValidationType } from '../../../../api/typings';
import { TaskStatus } from '../../../../api/typings/tasks';
import { createTooltip } from './utils';
import { ConfirmModal } from './confirm-modal/confirm-modal';
import { useUuiContext } from '@epam/uui-core';

type TaskSidebarProps = {
    viewMode: boolean;
    isValidation: boolean;
    allValidated: boolean;
    isAnnotatable: boolean;
    isSplitValidation: boolean;
    isNextTaskPresented?: boolean;
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
    isSplitValidation,
    notProcessedPages,
    isNextTaskPresented,
    onFinishValidation,
    onAnnotationTaskFinish,
    onFinishSplitValidation,
    jobType,
    taskStatus
}) => {
    const [redirectionSettings, setRedirectionSettings] = useState(
        localStorage.getItem('submitted-task-redirection-page') ?? 'tasks'
    );

    const confirmWindowNeed = process.env.REACT_APP_FINISH_LABELING_CONFIRM;

    const handleSetRedirectionSettings = (value: 'tasks' | 'next-task') => {
        setRedirectionSettings(value);
        localStorage.setItem('submitted-task-redirection-page', value);
    };

    const handleFinishValidation = isSplitValidation ? onFinishSplitValidation : onFinishValidation;
    const { uuiModals } = useUuiContext();

    const isDisabled = !isAnnotatable || (isValidation && !allValidated);

    const tooltipContent = createTooltip({
        isDisabled,
        isExtensiveCoverage: jobType === ValidationType.extensiveCoverage,
        notProcessedPages,
        taskStatus
    });

    const redirectSettingsDataSource = useArrayDataSource(
        {
            items: [
                { id: 'tasks', caption: 'Redirect to the Tasks page after submit' },
                { id: 'next-task', caption: 'Redirect to the next Task after submit' }
            ]
        },
        []
    );

    const finishingValidation = () => {
        if (isValidation) {
            handleFinishValidation();
        } else {
            onAnnotationTaskFinish();
        }
    };

    const showConfirmModal = () => {
        if (confirmWindowNeed === 'true' && !isValidation) {
            uuiModals
                .show<string>((props) => <ConfirmModal {...props} />)
                .then(() => {
                    finishingValidation();
                });
        } else {
            finishingValidation();
        }
    };

    return !isValidation && viewMode ? null : (
        <>
            <ControlGroup cx={styles['button-finish-control-group']}>
                <Tooltip content={tooltipContent}>
                    <Button
                        isDisabled={isDisabled}
                        cx={styles['button-finish']}
                        caption={isValidation ? 'FINISH VALIDATION' : 'FINISH LABELING'}
                        onClick={() => {
                            showConfirmModal();
                        }}
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
        </>
    );
};
