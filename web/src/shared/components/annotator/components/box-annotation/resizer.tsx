import React from 'react';
import styles from './box-annotation.module.scss';
import { ANNOTATION_RESIZER_CLASS } from './box-annotation';

export const Resizer = ({ color }: { color: string }) => (
    <>
        <div
            style={{ borderColor: color }}
            className={`${styles.resizer} ${styles['top-left']} ${ANNOTATION_RESIZER_CLASS} top-left`}
        />
        <div
            style={{ borderColor: color }}
            className={`${styles.resizer} ${styles['top-right']} ${ANNOTATION_RESIZER_CLASS} top-right`}
        />
        <div
            style={{ borderColor: color }}
            className={`${styles.resizer} ${styles['bottom-left']} ${ANNOTATION_RESIZER_CLASS} bottom-left`}
        />
        <div
            style={{ borderColor: color }}
            className={`${styles.resizer} ${styles['bottom-right']} ${ANNOTATION_RESIZER_CLASS} bottom-right`}
        />
    </>
);
