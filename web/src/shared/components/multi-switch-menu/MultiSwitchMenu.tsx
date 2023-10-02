// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { FC } from 'react';
import { MultiSwitch } from '@epam/loveship';
import { useHistory } from 'react-router-dom';
import capitalize from 'lodash/capitalize';

type MultiSwitchMenuProps = {
    items: string[];
    currentPath: string;
};

export const MultiSwitchMenu: FC<MultiSwitchMenuProps> = ({ items, currentPath }) => {
    const history = useHistory();

    const mappedItems = items.map((item, index) => ({
        id: index,
        caption: capitalize(item),
        path: `/${item}`
    }));

    const initialIndex = mappedItems.findIndex((item) => currentPath.indexOf(`${item.path}`) === 0);

    return (
        <MultiSwitch
            size="30"
            items={mappedItems}
            value={mappedItems[initialIndex].id}
            onValueChange={(newId) => {
                const currentItem = mappedItems.find((item) => item.id === newId);
                if (currentItem) {
                    history.push(currentItem.path);
                }
            }}
        />
    );
};
