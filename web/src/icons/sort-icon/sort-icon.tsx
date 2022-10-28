import React, { FC } from 'react';
import { ReactComponent as SortAsc } from '@epam/assets/icons/common/table-sort_asc-18.svg';
import { ReactComponent as SortDesc } from '@epam/assets/icons/common/table-sort_desc-18.svg';
import { SortingDirection } from 'api/typings';
import styles from './sort-icon.module.scss';

type SortIconProps = {
    sortDirection: SortingDirection;
    handleSorting: () => void;
};
export const SortIcon: FC<SortIconProps> = ({ sortDirection, handleSorting }) => {
    if (sortDirection === SortingDirection.ASC) {
        return <SortAsc className={styles['sort-icon']} onClick={handleSorting} />;
    } else {
        return <SortDesc className={styles['sort-icon']} onClick={handleSorting} />;
    }
};
