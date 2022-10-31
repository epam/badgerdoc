import React, { FC } from 'react';
import { Basement } from '../../../api/typings';
import styles from './basement-popup.module.scss';
import { IconContainer } from '@epam/loveship';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-close-24.svg';

type BasementPopupProps = {
    basement?: Basement;
    onClose: () => void;
};

const BasementPopup: FC<BasementPopupProps> = ({ basement, onClose }) => {
    return (
        <>
            <div className={styles.container} />
            <div className={styles.popup}>
                <IconContainer cx={styles.close} icon={closeIcon} onClick={onClose} />
                <div className="flex-row">
                    <div className={styles.title}>
                        <h3>{basement?.id}</h3>
                    </div>
                </div>
                <div className={styles.divider} />
                <h3>Supported arguments</h3>
                {basement?.supported_args?.map((el) => (
                    <div key={el.name} className={`flex-row ${styles.argument}`}>
                        <div className={styles.name}>{el.name}</div>
                        <div className={styles.type}>{el.type}</div>
                    </div>
                ))}
            </div>
        </>
    );
};

export default BasementPopup;
