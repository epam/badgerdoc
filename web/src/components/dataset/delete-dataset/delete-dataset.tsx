// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import { IconButton } from '@epam/loveship';
import React, { FC } from 'react';
import { ReactComponent as deleteIcon } from '@epam/assets/icons/common/content-clear-18.svg';
import { Dataset } from 'api/typings';
import styles from './delete-dataset.module.scss';

type DeleteDatasetProps = {
    dataset: Dataset;
    onDeleteDataset: (dataset: Dataset) => void;
    className: string;
};
export const DeleteDataset: FC<DeleteDatasetProps> = ({ dataset, onDeleteDataset, className }) => (
    <IconButton icon={deleteIcon} cx={styles[className]} onClick={() => onDeleteDataset(dataset)} />
);
