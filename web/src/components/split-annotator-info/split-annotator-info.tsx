import React, { FC } from 'react';
import styles from './split-annotator-info.module.scss';
import { Label } from 'api/typings';
import { SplitLabelsPanel } from 'components/split-labels-panel';

type SplitAnnotatorInfoProps = {
    annotatorName: string;
    labels: Label[];
    selectedLabelsId: string[];
};

export const SplitAnnotatorInfo: FC<SplitAnnotatorInfoProps> = ({
    annotatorName,
    labels,
    selectedLabelsId
}) => {
    return (
        <div className={styles.container}>
            <span className={styles.annotatorName}>{annotatorName}</span>
            <SplitLabelsPanel labels={labels} selectedLabelsId={selectedLabelsId} />
        </div>
    );
};
