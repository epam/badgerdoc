import { PluginType } from "api/typings";

export const isValidUrl = (url: string): boolean => {
    return /^http:\/\/[^\s/$.?#].[^\s]*$/i.test(url);
};

export const getDefaultValues = (plugin: PluginType | undefined) => {
        const {
            url = '',
            name = '',
            menu_name = '',
            description = '',
            version = '',
            is_iframe = true
        } = plugin || {};

        return {
            name,
            menu_name,
            description,
            version,
            url,
            is_iframe
        };
    };