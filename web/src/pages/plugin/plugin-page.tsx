import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Panel, Text as ErrorText, Blocker } from '@epam/loveship';
import { usePluginById } from 'api/hooks/plugins';
import { IframePage } from 'pages/iframe/iframe-page';
import { getError } from 'shared/helpers/get-error';

export const PluginPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();

    const { data: plugin, isLoading, error } = usePluginById(id);

    useEffect(() => {
        if (plugin && !plugin.is_iframe) {
            window.open(plugin.url, '_blank', 'noopener,noreferrer');
        }
    }, [plugin]);

    if (error || !plugin) {
        return (
            <Panel>
                <ErrorText>{getError(error)}</ErrorText>
            </Panel>
        );
    }

    if (!plugin.is_iframe) return null;

    return (
        <>
            <Blocker isEnabled={isLoading} />
            <IframePage src={plugin.url} title={plugin.menu_name || plugin.name} />
        </>
    );
};
