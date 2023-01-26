import React from 'react';
import styles from './no-data.module.scss';

interface NoDataProps {
    title?: string;
}

export const NoData = ({ title }: NoDataProps) => (
    <div className={styles.container}>
        <img src="/svg/S_No_items_found.svg" alt="No items found" width={'calc(100% / 2)'} />
        <p>{title ?? 'Nothing was found'}</p>
    </div>
);
