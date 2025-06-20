import { Panel, Text as ErrorText, Blocker } from '@epam/loveship';
import { usePluginById } from 'api/hooks/plugins';
import { IframePage } from 'pages/iframe/iframe-page';
import { useParams } from 'react-router-dom';
import { getError } from 'shared/helpers/get-error';

export const PluginPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();

    const { data: plugin, isLoading, error } = usePluginById(id);

    if (error || !plugin) {
        return (
            <Panel>
                <ErrorText>{getError(error)}</ErrorText>
            </Panel>
        );
    }

    if (!plugin.is_iframe) {
        return (
            <Panel>
                <ErrorText>This plugin must be opened in a new tab</ErrorText>
            </Panel>
        );
    }

    return (
        <>
            <Blocker isEnabled={isLoading} />
            <IframePage src={plugin.url} title={plugin.menu_name || plugin.name} />
        </>
    );
};
