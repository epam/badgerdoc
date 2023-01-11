import {
    DropdownMenuBody,
    DropdownMenuButton,
    Dropdown,
    Text,
    IconButton,
    DropdownMenuSplitter,
    FlexRow
} from '@epam/loveship';
import React, { ReactNode } from 'react';
import { DropdownBodyProps } from '@epam/uui-components';
import { ReactComponent as MoreIcon } from '@epam/assets/icons/common/navigation-more_vert-18.svg';
import { DataColumnProps } from '@epam/uui';
import { Model } from '../../api/typings';
import { ReactComponent as PencilIcon } from '@epam/assets/icons/common/content-edit-18.svg';
import { mapStatusForModels } from '../../shared/helpers/map-statuses';
import { Status } from 'shared/components/status';
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

export const modelsColumns: DataColumnProps<Model>[] = [
    {
        key: 'name',
        caption: 'Name',
        render: (model: Model) => <Text fontSize="14">{model.name}</Text>,
        isSortable: true,
        grow: 3,
        shrink: 2,
        width: 100
    },
    {
        key: 'tenant',
        caption: 'Tenant',
        grow: 1,
        shrink: 1,
        isSortable: true,
        render: (model: Model) => <Text fontSize="14">{model.tenant}</Text>,
        width: 100
    },
    {
        key: 'status',
        caption: 'Status',
        grow: 1,
        shrink: 1,
        isSortable: true,
        render: (model: Model) => (
            <FlexRow cx="align-baseline">
                {model.status && (
                    <Status
                        statusTitle={model.status}
                        color={mapStatusForModels(model?.status).color}
                    />
                )}
            </FlexRow>
        ),
        width: 100
    },
    {
        key: 'type',
        caption: 'Type',
        grow: 1,
        shrink: 1,
        isSortable: true,
        render: (model: Model) => <Text fontSize="14">{model.type}</Text>,
        width: 100
    },
    {
        key: 'score',
        caption: 'Score',
        grow: 1,
        shrink: 1,
        isSortable: true,
        render: (model: Model) => <Text fontSize="14">{model.score}</Text>,
        width: 100
    },
    {
        key: 'basement',
        caption: 'Basement',
        grow: 3,
        shrink: 1,
        isSortable: true,
        render: (model: Model) => <Text fontSize="14">{model.basement}</Text>,
        width: 100
    },
    {
        key: 'created_at',
        caption: 'Created',
        grow: 1,
        shrink: 1,
        isSortable: true,
        render: (model: Model) => (
            <Text fontSize="14">
                {model.created_at ? new Date(model.created_at).toLocaleDateString() : ''}
            </Text>
        ),
        width: 100
    },
    {
        key: 'created_by',
        caption: 'Author',
        grow: 2,
        shrink: 1,
        isSortable: true,
        render: (model: Model) => <Text fontSize="14">{model.created_by}</Text>,
        width: 100
    },
    {
        key: 'actions',
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        render: (model: Model) => (
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
