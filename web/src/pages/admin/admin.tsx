import React, { FC } from 'react';
import envInfo from 'env-info.json';
import styles from './admin.module.scss';

export const AdminPage: FC = () => {
    return (
        <div className={styles.content}>
            <h1>General Info</h1>
            <div>Last Commit Hash: {envInfo.lastCommitHash}</div>
        </div>
    );
};
