import React, { useMemo, useState } from 'react';
import { FlexSpacer, IconButton, FlexRow } from '@epam/loveship';
import styles from './sidebar.module.scss';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-back-18.svg';

export type SidebarProps = {
    title?: React.ReactNode;
    sideContent: React.ReactNode;
    mainContent: React.ReactNode;
    sidebarHeaderContent?: React.ReactNode;
};

export const Sidebar = ({
    title,
    sideContent,
    mainContent,
    sidebarHeaderContent
}: SidebarProps) => {
    const [isOpened, setIsOpened] = useState(true);

    const toggle = () => setIsOpened((v) => !v);

    const sidebarPanelClassname = useMemo(
        () =>
            `${styles['sidebar-panel-wrapper']} ${
                isOpened ? styles['sidebar-panel-opened'] : styles['sidebar-panel-closed']
            }`,
        [isOpened, styles]
    );

    const iconClassname = useMemo(
        () => `${styles['icon']} ${isOpened ? styles['close-icon'] : styles['open-icon']}`,
        [isOpened, styles]
    );

    const h2Classname = useMemo(
        () => `${styles['h2']} ${isOpened ? styles['h2-opened'] : styles['h2-closed']}`,
        [isOpened, styles]
    );

    return (
        <FlexRow alignItems="top" cx={styles['sidebar-wrapper']}>
            <div className={sidebarPanelClassname}>
                {sideContent}
                <IconButton cx={iconClassname} icon={closeIcon} onClick={toggle} color="sky" />
            </div>
            <div className={styles['content-container']}>
                <div className={`${styles['title']} ${h2Classname}`}>
                    {title ? (
                        <FlexRow>
                            {title}
                            <FlexSpacer></FlexSpacer>
                            {sidebarHeaderContent}
                        </FlexRow>
                    ) : (
                        <>
                            <div className={styles['content-container-documentpage']}>
                                {sidebarHeaderContent}
                            </div>
                        </>
                    )}
                </div>
                {mainContent}
            </div>
        </FlexRow>
    );
};
