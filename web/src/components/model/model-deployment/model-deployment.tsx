import React from 'react';
import { FlexCell } from '@epam/loveship';
import styles from './model-deployment.module.scss';
import { ModelDeployment } from 'api/typings';

type ModelDeployProps = {
    deployment: ModelDeployment;
};

export const ModelDeploy: React.FC<ModelDeployProps> = ({ deployment }) => {
    return (
        <div className={styles.container}>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>URL</span>
                </FlexCell>
                <FlexCell grow={1}>{deployment?.url || 'null'}</FlexCell>
            </div>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>Resource version</span>
                </FlexCell>
                <FlexCell grow={1}>{deployment?.resourceVersion || 'null'}</FlexCell>
            </div>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>Image</span>
                </FlexCell>
                <FlexCell grow={1}>{deployment?.image || 'null'}</FlexCell>
            </div>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>Service name</span>
                </FlexCell>
                <FlexCell grow={1}>{deployment?.container_name || 'null'}</FlexCell>
            </div>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>Created at</span>
                </FlexCell>
                <FlexCell grow={1}>{deployment?.datetime_creation || 'null'}</FlexCell>
            </div>
        </div>
    );
};
