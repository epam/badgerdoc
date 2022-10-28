import React, { FC, ReactNode } from 'react';
import { ReactComponent as Done } from '@epam/assets/icons/common/notification-check-fill-18.svg';
import styles from './wizard-step.module.scss';

type WizardStepProps = {
    stepTitle: string;
    currentStep: number;
    stepNumber: number;
};

const WizardStep: FC<WizardStepProps> = ({ stepTitle, currentStep, stepNumber }) => {
    let icon: ReactNode;
    if (stepNumber < currentStep) {
        icon = <Done className={styles.done} />;
    } else if (stepNumber === currentStep) {
        icon = <div className={styles.circle}>{stepNumber + 1}</div>;
    } else {
        icon = <div className={`${styles.circle} ${styles.gray}`}>{stepNumber + 1}</div>;
    }
    return (
        <div className={`${styles.step} flex`}>
            <div className={`${styles.icon} flex`}>{icon}</div>
            <div className={`${styles['step-name']} flex`}>{stepTitle}</div>
        </div>
    );
};

export default WizardStep;
