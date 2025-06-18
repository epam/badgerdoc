// temporary_disabled_rules
/* eslint-disable react-hooks/rules-of-hooks, @typescript-eslint/no-unused-expressions */
import { useBadgerFetch } from "./api";
import { PLUGINS_API } from "shared/constants/api";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { CreatePlugin, MutationHookType, PluginType } from "api/typings";

type PluginResponse = {
    plugins: PluginType[];
};

type UpdatePluginPayload = {
    menu_name: string,
    description: string,
    url: string;
    is_iframe: boolean;
};

export async function pluginsFetcher(): Promise<PluginResponse> {
    const badgerFetcher = useBadgerFetch;
    return badgerFetcher<PluginResponse>({
        url: PLUGINS_API,
        method: 'get',
        withCredentials: true
    })();
}

export const usePlugins = () => {
    return useQuery<PluginResponse, Error, PluginType[]>(
        ['plugins'],
        pluginsFetcher,
        {
            select: (data) => data.plugins
        }
    );
};

export const addPlugin = async (data: CreatePlugin): Promise<PluginType> => {
    return useBadgerFetch<PluginType>({
        url: PLUGINS_API,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(data));
};

export const useAddPluginMutation: MutationHookType<CreatePlugin, any> = () => {
    const queryClient = useQueryClient();

    return useMutation(addPlugin, {
        onSuccess: () => {
            queryClient.invalidateQueries('plugins');
        }
    });
};

export const updatePlugin = async (
    id: number,
    data: UpdatePluginPayload
): Promise<PluginType> => {
    return useBadgerFetch<PluginType>({
        url: `${PLUGINS_API}/${id}`,
        method: 'put',
        withCredentials: true
    })(JSON.stringify(data));
};

export const useUpdatePluginMutation: MutationHookType<
    { id: number; data: UpdatePluginPayload },
    any
> = () => {
    const queryClient = useQueryClient();

    return useMutation(({ id, data }) => updatePlugin(id, data), {
        onSuccess: () => {
            queryClient.invalidateQueries('plugins');
        }
    });
};
