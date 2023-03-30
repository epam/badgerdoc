import React from 'react';
import { ReactComponent as searchIcon } from '@epam/assets/icons/common/action-search-12.svg';
import { Button, IconContainer } from '@epam/loveship';
import styles from './document-scale.module.scss';
import { cx } from '@epam/uui';

type TScaleProps = {
    scale: number;
    onChange: (value: React.SetStateAction<number>) => void;
};

export const DocumentScale: React.FC<TScaleProps> = ({ scale, onChange }) => (
    <div className={styles.container}>
        <Button
            fill="white"
            color="night600"
            size="24"
            caption="+"
            onClick={() => onChange((origin) => origin + 0.1)}
            cx={cx(styles.button, scale > 0 && styles.active)}
        />
        <IconContainer icon={searchIcon} cx={styles.icon} />
        <Button
            fill="white"
            color="night600"
            size="24"
            caption="-"
            onClick={() => onChange((origin) => origin - 0.1)}
            cx={cx(styles.button, styles.marginBottom, scale < 0 && styles.active)}
        />
    </div>
);
