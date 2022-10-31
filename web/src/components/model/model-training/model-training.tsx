import { Model, Training } from 'api/typings';
import React from 'react';
import { ProgressBar } from '../../../shared/components/progress-bar/progress-bar';
import { FlexCell, FlexRow } from '@epam/loveship';
import styles from './model-training.module.scss';
import { TrainingJobsConnector } from '../../../connectors/training-jobs-connector/training-jobs-connector';

type ModelTrainingParams = {
    model: Model;
    training: Training;
};

export const ModelTraining: React.FC<ModelTrainingParams> = ({ model, training }) => {
    return (
        <FlexRow alignItems="top" spacing="18">
            <div className={styles.container}>
                <div className={styles.row}>
                    <FlexCell width={200}>
                        <span className={styles.title}>Training status</span>
                    </FlexCell>
                    <FlexCell grow={1}>null</FlexCell>
                </div>
                <div className={styles.row}>
                    <FlexCell width={200}>
                        <span className={styles.title}>Training name</span>
                    </FlexCell>
                    <FlexCell grow={1}>{training?.name || 'null'}</FlexCell>
                </div>
                <div className={styles.row}>
                    <FlexCell width={200}>
                        <span className={styles.title}>Training mode</span>
                    </FlexCell>
                    <FlexCell grow={1}>null</FlexCell>
                </div>
                <div className={styles.row}>
                    <FlexCell width={200}>
                        <span className={styles.title}>Epoch count</span>
                    </FlexCell>
                    <FlexCell grow={1}>{training?.epochs_count || 'null'}</FlexCell>
                </div>
                <div className={styles.row}>
                    <FlexCell width={200}>
                        <span className={styles.title}>Basement</span>
                    </FlexCell>
                    <FlexCell grow={1}>{training?.basement || 'null'}</FlexCell>
                </div>
                <div className={styles.row}>
                    <FlexCell width={200}>
                        <span className={styles.title}>Kuberflow pipeline id</span>
                    </FlexCell>
                    <FlexCell grow={1}>{training?.kuberflow_pipeline_id || 'null'}</FlexCell>
                </div>
                <div className={styles.row}>
                    <FlexCell width={200}>
                        <span className={styles.title}>Created at</span>
                    </FlexCell>
                    <FlexCell grow={1}>{training?.created_at || 'null'}</FlexCell>
                </div>
                <div className={styles.row}>
                    <FlexCell width={200}>
                        <span className={styles.title}>Created by</span>
                    </FlexCell>
                    <FlexCell grow={1}>{training?.created_by || 'null'}</FlexCell>
                </div>
                <div className={styles.row}>
                    <FlexCell width={200}>
                        <span className={styles.title}>Tenant</span>
                    </FlexCell>
                    <FlexCell grow={1}>{training?.tenant || 'null'}</FlexCell>
                </div>
            </div>
            <FlexCell alignSelf="flex-start" textAlign="center" minWidth={200} cx="m-l-20">
                <ProgressBar value={model?.score || 0} />
                <span className={styles.score}>Score</span>
            </FlexCell>
            <FlexCell minWidth={200} cx="m-l-20" grow={1}>
                <TrainingJobsConnector jobs={training?.jobs || []} />
            </FlexCell>
        </FlexRow>
    );
};
