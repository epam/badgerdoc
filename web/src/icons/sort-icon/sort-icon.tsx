// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC } from 'react';
import { ReactComponent as SortAsc } from '@epam/assets/icons/common/table-sort_asc-18.svg';
import { ReactComponent as SortDesc } from '@epam/assets/icons/common/table-sort_desc-18.svg';
import { SortingDirection } from 'api/typings';
import { IconButton } from '@epam/loveship';

type SortIconProps = {
    sortDirection: SortingDirection;
    handleSorting: () => void;
};
export const SortIcon: FC<SortIconProps> = ({ sortDirection, handleSorting }) => {
    if (sortDirection === SortingDirection.ASC) {
        return <IconButton icon={SortAsc} onClick={handleSorting} />;
    } else {
        return <IconButton icon={SortDesc} onClick={handleSorting} />;
    }
};
