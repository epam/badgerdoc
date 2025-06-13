import { Button, DataTable, Panel } from '@epam/loveship';
import { PluginType } from 'api/typings';
import { usePlugins } from 'api/hooks/plugins';
import { TableWrapper, usePageTable } from 'shared';
import { useArrayDataSource, useUuiContext } from '@epam/uui';
import { PluginModal } from 'connectors/plugins-modal-connector/plugins-modal-connector';
import { PluginValidationValues } from 'connectors/plugins-modal-connector/types';
import { pluginsColumns } from './plugin-columns';

import styles from './plugins-table-connector.module.scss';

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
                    columns={pluginsColumns}
                    headerTextCase="upper"
                />
            </TableWrapper>
        </Panel>
    );
};
