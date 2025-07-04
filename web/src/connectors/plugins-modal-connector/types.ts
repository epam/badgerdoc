import { IModal } from '@epam/uui';
import { PluginType } from 'api/typings';

export interface PluginValidationValues {
    pluginValue?: PluginType;
}

export interface IPluginProps extends IModal<PluginValidationValues> {
    pluginValue?: PluginType;
}

export type TPluginFormValues = {
    name: string;
    menu_name: string;
    description: string;
    version: string;
    url: string;
    is_iframe: boolean;
};
