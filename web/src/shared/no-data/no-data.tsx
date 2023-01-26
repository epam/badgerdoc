import React from 'react';
import styles from './no-data.module.scss';

interface NoDataProps {
    title?: string;
}

export const NoData = ({ title }: NoDataProps) => (
    <div className={styles.container}>
        <p>{title ?? 'Nothing was found'}</p>
        <img src="/svg/S_No_items_found.svg" alt="No items found" height={131} />
    </div>
);
