import { IconButton, Text as UiText } from '@epam/loveship';
import { PluginType } from 'api/typings';
import { ReactComponent as DeleteIcon } from '@epam/assets/icons/common/action-delete-18.svg';

export const pluginsColumns = [
    {
        key: 'name',
        caption: 'Name',
        render: (plugin: PluginType) => {
            return (
                <UiText key={plugin.name}>
                    <div>{plugin.name}</div>
                </UiText>
            );
        },
        isSortable: true,
        grow: 1,
        shrink: 1,
        width: 100
    },
    {
        key: 'name',
        caption: 'Delete',
        render: (plugin: PluginType) => {
            return (
                <UiText key={plugin.name}>
                    <IconButton icon={DeleteIcon} onClick={() => {}} />
                </UiText>
            );
        },
        isSortable: true,
        justifyContent: 'center',
        grow: 0,
        shrink: 1,
        width: 100
    }
];
