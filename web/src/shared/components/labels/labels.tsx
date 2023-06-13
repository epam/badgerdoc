import React, { FC, useCallback } from 'react';
import { Dropdown, Button, DropdownContainer } from '@epam/loveship';
import { LabelRow } from '../../../components/task/task-sidebar-flow/label-row';
import { useLabels } from 'shared/hooks/use-labels';
import { Label } from 'api/typings';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import { OWNER_TAB } from '../../../components/task/task-sidebar-flow/constants';

export const Labels: FC = () => {
    const { currentTab, labels } = useLabels();
    const { selectedLabels, onLabelsSelected, setTabValue } = useTaskAnnotatorContext();

    const handleLabelDelete = useCallback(
        (label: Label) => {
            const withoutCurrentLabel = selectedLabels.filter(({ id }) => id !== label.id);
            onLabelsSelected(withoutCurrentLabel);
        },
        [onLabelsSelected, selectedLabels]
    );

    const handleLabelSelect = useCallback(
        (label: Label) => {
            const isExisted = selectedLabels.some(({ id }) => id === label.id);

            if (!isExisted) {
                setTabValue('Document');
                onLabelsSelected([...selectedLabels, label]);
            }
        },
        [onLabelsSelected, selectedLabels]
    );

    const isEditable = currentTab === OWNER_TAB.id;

    return (
        <>
            {!!labels.length && (
                <Dropdown
                    renderBody={() => (
                        <DropdownContainer vPadding="12" padding="6">
                            {labels.map((label) => (
                                <LabelRow
                                    key={label.id}
                                    label={label}
                                    isEditable={isEditable}
                                    onClick={handleLabelSelect}
                                    onDelete={handleLabelDelete}
                                />
                            ))}
                        </DropdownContainer>
                    )}
                    renderTarget={(props) => (
                        <Button
                            fill="white"
                            size="24"
                            caption={`Labels (${labels.length})`}
                            {...props}
                        />
                    )}
                    closeOnTargetClick={false}
                />
            )}
        </>
    );
};
