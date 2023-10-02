// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC } from 'react';
import { Button } from '@epam/loveship';
import { ReactComponent as plusIcon } from '@epam/assets/icons/common/action-add-18.svg';
import styles from './sidebar-button.module.scss';

type SidebarButtonProps = {
    onClick: () => void;
    caption: string;
};
const SidebarButton: FC<SidebarButtonProps> = ({ onClick, caption }) => {
    return (
        <Button
            cx={styles['button']}
            icon={plusIcon}
            color="sky"
            caption={caption}
            size="36"
            onClick={onClick}
        />
    );
};
export default SidebarButton;
