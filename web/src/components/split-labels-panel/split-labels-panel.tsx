import React, { FC } from 'react';
import { Tag } from '@epam/loveship';
import styles from './split-labels-panel.module.scss';
import { Label } from 'api/typings';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
type SplitLabelsPanelProps = {
    labels: Label[];
    selectedLabelsId: string[];
};

export const SplitLabelsPanel: FC<SplitLabelsPanelProps> = ({ labels, selectedLabelsId }) => {
    const { setTabValue, onLabelsSelected } = useTaskAnnotatorContext();

    const onClick = (id: string) => () => {
        setTabValue('Document');
        onLabelsSelected(labels, [...selectedLabelsId, id]);
    };

    return (
        <div className={styles.container}>
            {labels?.map(({ name, id }) => (
                <Tag size="24" caption={name} key={name} onClick={onClick(id)} cx={styles.tag} />
            ))}
        </div>
    );
};
