import { Button, DataTable, Panel, Text as UiText } from '@epam/loveship';
import { PluginType } from 'api/typings';
import { usePlugins } from 'api/hooks/plugins';
import { TableWrapper, usePageTable } from 'shared';
import { useArrayDataSource, useUuiContext } from '@epam/uui';
import { PluginModal } from 'connectors/plugins-modal-connector/plugins-modal-connector';
import { PluginValidationValues } from 'connectors/plugins-modal-connector/types';

import styles from './plugins-table-connector.module.scss';

const columns = [
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
        width: 300
    }
];

export const PluginsTableConnector = () => {
    const { tableValue, onTableValueChange, onPageChange, totalCount, pageConfig } =
        usePageTable<PluginType>('name');

    const { page, pageSize } = pageConfig;

    const { data } = usePlugins();
    const pluginsSource = useArrayDataSource<PluginType, number, unknown>(
        {
            items: data ?? []
        },
        [data]
    );

    //@ts-ignore
    const view = pluginsSource.useView(tableValue, onTableValueChange, {
        getRowOptions: () => ({
            isSelectable: true,
            onClick: (item) => {
                return uuiModals.show<PluginValidationValues>((props) => (
                    <PluginModal pluginValue={item.value} {...props} />
                ));
            }
        })
    });
    const { uuiModals } = useUuiContext();

    return (
        <Panel cx={`${styles['container']} flex-col`}>
            <div className={`${styles['title']} flex justify-end align-vert-center`}>
                <Button
                    onClick={() =>
                        uuiModals.show<PluginValidationValues>((props) => (
                            <PluginModal {...props} />
                        ))
                    }
                    caption="Add Plugin"
                />
            </div>
            <TableWrapper
                page={page}
                pageSize={pageSize}
                totalCount={totalCount}
                onPageChange={onPageChange}
            >
                <DataTable
                    {...view.getListProps()}
                    getRows={view.getVisibleRows}
                    value={tableValue}
                    onValueChange={onTableValueChange}
                    columns={columns}
                    headerTextCase="upper"
                />
            </TableWrapper>
        </Panel>
    );
};
