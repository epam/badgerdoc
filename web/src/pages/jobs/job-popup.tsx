import styles from './job-popup.module.scss';
import { Button, Checkbox, IconContainer, SearchInput, TextInput } from '@epam/loveship';
import React, { useState, useEffect } from 'react';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-close-24.svg';

interface JobPopupProps {
    popupType: 'extraction' | 'annotation' | null;
    closePopup: () => void;
    selectedFiles: number[];
}

const JobPopup: React.FC<JobPopupProps> = ({ popupType, closePopup, selectedFiles }) => {
    const [searchDataset, searchDatasetChange] = useState<string>('');
    const [searchPipeline, searchPipelineChange] = useState<string>('');
    const [hasOnlySelectedDoc, hasOnlySelectedDocChange] = useState<boolean>(false);
    const [validators, validatorsChange] = useState<string | undefined>('1');

    useEffect(() => {
        if (selectedFiles && selectedFiles.length > 0) {
            hasOnlySelectedDocChange(true);
        } else {
            hasOnlySelectedDocChange(false);
        }
    }, [selectedFiles]);

    return (
        <>
            <div className={styles.container}></div>
            <div className={styles.popup}>
                <IconContainer cx={styles.close} icon={closeIcon} onClick={() => closePopup()} />
                <div className="flex-row">
                    <div className={styles.dataset}>
                        <h3>Dataset</h3>
                        <SearchInput
                            cx={styles.search}
                            value={searchDataset}
                            onValueChange={(newValue: string) => searchDatasetChange(newValue)}
                            placeholder="Search dataset"
                            size="30"
                        />
                        <div className={styles.list}></div>
                        <Checkbox
                            cx="m-t-30 m-b-10"
                            size="18"
                            label="Only selected document"
                            value={hasOnlySelectedDoc}
                            onValueChange={hasOnlySelectedDocChange}
                        />
                        <TextInput
                            cx={styles.input}
                            value={validators}
                            onValueChange={validatorsChange}
                            placeholder={'Document name or ID'}
                        />

                        {popupType === 'annotation' ? (
                            <>
                                <h3 className="m-t-13">Labels</h3>
                                <div className={styles.list}></div>
                                <Button
                                    cx={styles.button}
                                    caption="Create without assignment"
                                    onClick={() => null}
                                />
                            </>
                        ) : null}
                    </div>

                    <div className={styles.pipeline}>
                        <h3>Pipeline</h3>
                        <SearchInput
                            cx={styles.search}
                            value={searchPipeline}
                            onValueChange={(newValue: string) => searchPipelineChange(newValue)}
                            placeholder="Search pipeline"
                            size="30"
                        />
                        <div className={styles.list}></div>

                        {popupType === 'annotation' ? (
                            <>
                                <h3 className="m-t-25">Validation</h3>
                                <div className="flex-row flex-center justify-between">
                                    <div className="m-r-28">Validators:</div>
                                    <TextInput
                                        cx={styles.input}
                                        value={validators}
                                        onValueChange={validatorsChange}
                                    />
                                </div>
                                <Button
                                    cx={styles.button}
                                    caption="Create and assign"
                                    onClick={() => null}
                                />
                            </>
                        ) : (
                            <Button
                                cx={styles.button}
                                caption="Start pipeline"
                                onClick={() => null}
                            />
                        )}
                    </div>
                </div>
            </div>
        </>
    );
};

export default JobPopup;
