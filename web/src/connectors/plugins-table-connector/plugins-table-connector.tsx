import {
    Button,
    DataTable,
    Panel,
    SuccessNotification,
    ErrorNotification,
    Text as UiText
} from '@epam/loveship';
import { PluginType } from 'api/typings';
import { useDeletePluginMutation, usePlugins } from 'api/hooks/plugins';
import { usePageTable } from 'shared';
import { useArrayDataSource, useUuiContext } from '@epam/uui';
import { PluginModal } from 'connectors/plugins-modal-connector/plugins-modal-connector';
import { PluginValidationValues } from 'connectors/plugins-modal-connector/types';
import { getPluginsColumns } from './plugin-columns';

import styles from './plugins-table-connector.module.scss';
import { ConfirmModal } from 'components/confirm-modal/confirm-modal';

export const PluginsTableConnector = () => {
    const { tableValue, onTableValueChange } = usePageTable<PluginType>('name');

    const { data } = usePlugins();
    const { uuiModals, uuiNotifications } = useUuiContext();
    const { mutate: deletePlugin } = useDeletePluginMutation();

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

    const showConfirmModal = (plugin: PluginType) => {
        if (plugin.is_autoinstalled) {
            uuiNotifications.show((props) => (
                <ErrorNotification {...props}>
                    <UiText>Cannot delete autoinstalled plugin!</UiText>
                </ErrorNotification>
            ));
            return;
        }
        uuiModals
            .show<string>((props) => (
                <ConfirmModal
                    modalProps={props}
                    confirmationText={`Are you sure you want to delete ${plugin.menu_name}?`}
                />
            ))
            .then(() => {
                deletePlugin(plugin.id, {
                    onSuccess: () => {
                        uuiNotifications.show((props) => (
                            <SuccessNotification {...props}>
                                <UiText>{plugin.menu_name} deleted successfully!</UiText>
                            </SuccessNotification>
                        ));
                    }
                });
            });
    };

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

            <DataTable
                {...view.getListProps()}
                getRows={view.getVisibleRows}
                value={tableValue}
                onValueChange={onTableValueChange}
                columns={getPluginsColumns(showConfirmModal)}
                headerTextCase="upper"
            />
        </Panel>
    );
};
