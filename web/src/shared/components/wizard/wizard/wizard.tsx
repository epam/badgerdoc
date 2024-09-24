// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC, Fragment } from 'react';
import WizardStep from '../wizard-step/wizard-step';
import { Link, useHistory } from 'react-router-dom';
import { ReactComponent as backIcon } from '@epam/assets/icons/common/navigation-back-24.svg';
import { Button, IconContainer } from '@epam/loveship';
import styles from './wizard.module.scss';

export type WizardPropsStep = {
    title: string;
    content: any;
};

type WizardProps = {
    steps: WizardPropsStep[];
    returnUrl: string;
    stepIndex: number;
    revisionId?: string | null;
};

export const renderWizardButtons = ({
    onPreviousClick,
    onNextClick,
    nextButtonCaption,
    disableNextButton
}: {
    onPreviousClick?: any;
    onNextClick: any;
    nextButtonCaption?: string;
    disableNextButton?: boolean;
}) => {
    return (
        <>
            {onPreviousClick ? (
                <Button fill="light" caption="Previous" onClick={onPreviousClick} />
            ) : null}
            <Button
                caption={nextButtonCaption || 'Next'}
                onClick={onNextClick}
                isDisabled={disableNextButton}
            />
        </>
    );
};

const Wizard: FC<WizardProps> = ({ steps, returnUrl, stepIndex, revisionId }) => {
    const currentStep = steps[stepIndex];
    const history = useHistory();
    return (
        <div className={styles.wrapper}>
            <div className={styles.header}>
                <div className={styles['back-link-wrapper']}>
                    {revisionId ? (
                        <Link
                            to={''}
                            onClick={(e) => {
                                e.preventDefault();
                                history.goBack();
                            }}
                        >
                            <div className={styles['back-icon']}>
                                <IconContainer icon={backIcon} color="sky" /> Back
                            </div>
                        </Link>
                    ) : (
                        <Link to={returnUrl}>
                            <div className={styles['back-icon']}>
                                <IconContainer icon={backIcon} color="sky" /> Back
                            </div>
                        </Link>
                    )}
                </div>

                <div className={`${styles['steps-wrapper']} flex flex-center`}>
                    {revisionId ? (
                        <p className={styles.title}>New job from revision {revisionId}</p>
                    ) : (
                        <>
                            {steps.map((step, idx) => {
                                return (
                                    <Fragment key={idx}>
                                        <WizardStep
                                            key={step.title}
                                            stepTitle={step.title}
                                            currentStep={stepIndex}
                                            stepNumber={idx}
                                        />
                                        {idx < steps.length - 1 ? (
                                            <div className={styles.divider} />
                                        ) : (
                                            ''
                                        )}
                                    </Fragment>
                                );
                            })}
                        </>
                    )}
                </div>
            </div>

            <div className={styles.content}>{currentStep.content}</div>
        </div>
    );
};

export default Wizard;
