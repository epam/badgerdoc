// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC, ReactElement } from 'react';
import { ReactComponent as Icon } from '@epam/assets/icons/common/notification-info-outline-18.svg';
import { Tooltip } from '@epam/loveship';
import styles from './info-icon.module.scss';

type InputInfoProps = {
    title: string;
    description: string | ReactElement;
};

export const InfoIcon: FC<InputInfoProps> = ({ title, description }) => {
    const renderCustomMarkup = () => (
        <>
            <div className={styles.title}>{title}</div>
            <div>{description}</div>
        </>
    );

    if (!title && !description) {
        return (
            <div className={styles.icon}>
                <Icon />
            </div>
        );
    }

    return (
        <div className={styles.icon}>
            <Tooltip content={renderCustomMarkup()}>
                <Icon />
            </Tooltip>
        </div>
    );
};
