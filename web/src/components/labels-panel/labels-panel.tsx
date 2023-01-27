import React, { FC } from 'react';
import { FlexCell, FlexRow, Tag, Button } from '@epam/loveship';
import styles from './labels-panel.module.scss';
import { Label } from 'api/typings';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';

type LabelsPanelProps = {
    labels?: Label[];
};

export const LabelsPanel: FC<LabelsPanelProps> = ({ labels }) => {
    if (!labels) {
        return <div>Loading...</div>;
    }
    const labelsName = labels.map((label) => label.name);

    const { setTabValue } = useTaskAnnotatorContext();
    return (
        <FlexCell width="auto" cx={styles.container}>
            <FlexRow alignItems="top" spacing="12">
                <Button
                    fill="white"
                    color="sky"
                    size="24"
                    caption="+ Add Labels"
                    onClick={() => setTabValue('Document')}
                    cx={styles.button}
                />
                {labelsName.map((label) => (
                    <Tag size="24" caption={label} key={label} />
                ))}
            </FlexRow>
        </FlexCell>
    );
};
