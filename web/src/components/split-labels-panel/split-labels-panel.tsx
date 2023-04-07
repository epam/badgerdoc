import React, { FC } from 'react';
import { Tag, Spinner } from '@epam/loveship';
import styles from './split-labels-panel.module.scss';
import { Label } from 'api/typings';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
type SplitLabelsPanelProps = {
    labels: Label[];
    selectedLabelsId: string[];
};

export const SplitLabelsPanel: FC<SplitLabelsPanelProps> = ({ labels, selectedLabelsId }) => {
    const { setTabValue, onLabelsSelected } = useTaskAnnotatorContext();

    if (!labels) {
        return <Spinner color="sky" />;
    }

    const onClick = (label: Label) => () => {
        setTabValue('Document');
        onLabelsSelected([label]);
    };

    return (
        <div className={styles.container}>
            {labels.map(({ name, id }) => (
                <Tag
                    size="24"
                    caption={name}
                    key={name}
                    onClick={onClick({ name, id })}
                    cx={styles.tag}
                />
            ))}
        </div>
    );
};
