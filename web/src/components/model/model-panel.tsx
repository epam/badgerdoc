import { Panel } from '@epam/loveship';
import React, { FC } from 'react';
import styles from './model-panel.module.scss';
interface IProps {
    children: React.ReactNode;
}
const ModelPanel: FC<IProps> = ({ children }) => {
    return <Panel cx={`${styles['container']} flex-col`}>{children}</Panel>;
};

export default ModelPanel;
