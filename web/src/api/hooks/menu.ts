import { MENU_API } from "shared/constants/api";
import { AppMenuItem } from "api/typings";
import { useQuery, UseQueryOptions } from "react-query";
import { useBadgerFetch } from "./api";

export async function menuItemsFetcher(): Promise<AppMenuItem[]> {
    const badgerFetcher = useBadgerFetch;
    return badgerFetcher<AppMenuItem[]>({
        url: MENU_API,
        method: 'get',
        withCredentials: true
    })();
}

export const useMenuItems = (options?: UseQueryOptions<AppMenuItem[], Error>) => {
    return useQuery<AppMenuItem[], Error>(
        ['menu'],
        menuItemsFetcher,
        {
            select: (data) => data,
            ...options
        }
    );
};
