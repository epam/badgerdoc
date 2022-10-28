import React from 'react';
import { Model } from 'api/typings';
import { FlexCell } from '@epam/loveship';
import styles from './model-info.module.scss';

type ModelInfoProps = {
    model: Model;
};

export const ModelInfo: React.FC<ModelInfoProps> = ({ model }) => {
    return (
        <div className={styles.container}>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>Name</span>
                </FlexCell>
                <FlexCell grow={1}>{model?.name || 'null'}</FlexCell>
            </div>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>ID</span>
                </FlexCell>
                <FlexCell grow={1}>{model?.id || 'null'}</FlexCell>
            </div>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>Basement</span>
                </FlexCell>
                <FlexCell grow={1}>{model?.basement || 'null'}</FlexCell>
            </div>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>Score</span>
                </FlexCell>
                <FlexCell grow={1}>{model?.score || 'null'}</FlexCell>
            </div>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>Type</span>
                </FlexCell>
                <FlexCell grow={1}>{model?.type || 'null'}</FlexCell>
            </div>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>Categories</span>
                </FlexCell>
                <FlexCell grow={1}>{model?.categories?.join(', ')}</FlexCell>
            </div>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>Created at</span>
                </FlexCell>
                <FlexCell grow={1}>{model?.created_at || 'null'}</FlexCell>
            </div>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>Created by</span>
                </FlexCell>
                <FlexCell grow={1}>{model?.created_by || 'null'}</FlexCell>
            </div>
            <div className={styles.row}>
                <FlexCell width={200}>
                    <span className={styles.title}>Tenant</span>
                </FlexCell>
                <FlexCell grow={1}>{model?.tenant || 'null'}</FlexCell>
            </div>
        </div>
    );
};
