import {
    Dropdown,
    DropdownMenuBody,
    DropdownMenuButton,
    DropdownMenuSplitter,
    IconButton,
    Text
} from '@epam/loveship';
import React, { ReactNode } from 'react';
import { Basement, SupportedArgs } from 'api/typings';
import { ReactComponent as PencilIcon } from '@epam/assets/icons/common/content-edit-18.svg';
import { ReactComponent as MoreIcon } from '@epam/assets/icons/common/navigation-more_vert-18.svg';
import { ReactComponent as CheckIcon } from '@epam/assets/icons/common/notification-check-fill-18.svg';
import { DataColumnProps } from '@epam/uui';
import { DropdownBodyProps } from '@epam/uui-components';

const renderArgumentsString = (args?: SupportedArgs[] | null) => {
    if (!args) return '';
    const textArguments = args.map((el, index) => {
        if (index < 3) {
            return `${el.name}: ${el.type}`;
        } else if (index === 3) {
            return `...`;
        } else return null;
    });
    return textArguments.join(', ');
};

const renderMenu = (props: DropdownBodyProps): ReactNode => (
    <DropdownMenuBody color="white">
        <DropdownMenuButton
            caption="Edit"
            icon={PencilIcon}
            onClick={(e) => {
                e.stopPropagation();
            }}
        />
        <DropdownMenuButton
            caption="Remove"
            onClick={(e) => {
                e.stopPropagation();
            }}
        />
        <DropdownMenuSplitter />
        <DropdownMenuButton caption="Cancel" onClick={props.onClose} />
    </DropdownMenuBody>
);

export const basementColumns: DataColumnProps<Basement>[] = [
    {
        key: 'name',
        caption: 'Basement name',
        render: (basement: Basement) => <Text fontSize="14">{basement.name}</Text>,
        isSortable: true,
        grow: 3,
        shrink: 2
    },
    {
        key: 'id',
        caption: 'ID',
        grow: 1,
        shrink: 1,
        isSortable: true,
        render: (basement: Basement) => <Text fontSize="14">{basement.id}</Text>
    },
    {
        key: 'tenant',
        caption: 'Tenant',
        grow: 1,
        shrink: 1,
        isSortable: true,
        render: (basement: Basement) => <Text fontSize="14">{basement.tenant}</Text>
    },
    {
        key: 'gpu_support',
        caption: 'GPU Support',
        grow: 1,
        shrink: 1,
        isSortable: true,
        render: (basement: Basement) =>
            basement.gpu_support ? (
                <Text fontSize="18" cx="m-r-15">
                    <CheckIcon />
                </Text>
            ) : null
    },
    {
        key: 'arguments',
        caption: 'Arguments',
        grow: 1,
        shrink: 1,
        isSortable: true,
        render: (basement: Basement) => (
            <Text fontSize="14">{renderArgumentsString(basement.supported_args)}</Text>
        )
    },
    {
        key: 'creation_at',
        caption: 'Created',
        render: (basement: Basement) => (
            <Text fontSize="14">
                {basement.created_at ? new Date(basement.created_at).toLocaleDateString() : ''}
            </Text>
        ),
        grow: 1,
        shrink: 1,
        isSortable: true
    },
    {
        key: 'created_by',
        caption: 'Author',
        grow: 1,
        shrink: 1,
        isSortable: true,
        render: (basement: Basement) => <Text fontSize="14">{basement.created_by}</Text>
    },
    {
        key: 'actions',
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        render: (basement: Basement) => (
            <Dropdown
                renderTarget={(props) => <IconButton icon={MoreIcon} {...props} />}
                renderBody={renderMenu}
                placement="bottom-end"
            />
        ),
        grow: 0,
        shrink: 0,
        width: 54,
        fix: 'right'
    }
];
