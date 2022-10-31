import styles from './paper.module.scss';
import React, { PropsWithChildren } from 'react';

type PaperProps = PropsWithChildren<{
    centered?: boolean;
    width?: string;
    height?: string;
    padding?: string;
}>;

export const Paper = ({ children, centered, width, height, padding }: PaperProps) => {
    const className: string = ([] as string[])
        .concat(centered ? styles.centered : [])
        .concat(styles.paper)
        .join(' ');

    return (
        <div style={{ width, height, padding }} className={className}>
            {children}
        </div>
    );
};
