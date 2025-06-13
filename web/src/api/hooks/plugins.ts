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
    name: string;
    menu_name: string;
    url: string;
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
            select: (data) => data.plugins.map((plugin) => ({
                    ...plugin,
                    id: plugin.name.toLowerCase()
                }))
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

const updatePlugin = async (data: UpdatePluginPayload): Promise<PluginType> => {
    const { name, ...rest } = data;
    return useBadgerFetch<PluginType>({
        url: `${PLUGINS_API}/${name}`,
        method: 'put',
        withCredentials: true,
    })(JSON.stringify(rest));
};

export const useUpdatePluginMutation: MutationHookType<UpdatePluginPayload, any> = () => {
    const queryClient = useQueryClient();

    return useMutation(updatePlugin, {
        onSuccess: () => {
            queryClient.invalidateQueries('plugins');
        }
    });
};
