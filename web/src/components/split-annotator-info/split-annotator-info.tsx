// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC } from 'react';
import styles from './split-annotator-info.module.scss';

type SplitAnnotatorInfoProps = {
    annotatorName: string;
};

export const SplitAnnotatorInfo: FC<SplitAnnotatorInfoProps> = ({ annotatorName }) => {
    return (
        <div className={styles.container}>
            <span className={styles.annotatorName}>{annotatorName}</span>
        </div>
    );
};
