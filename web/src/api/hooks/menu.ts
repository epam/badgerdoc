import { useEffect, useState } from "react";
import { isArray, isEmpty } from "lodash";

import { MENU_API } from "shared/constants/api";
import { AppMenuItem } from "api/typings";
import { getAuthHeaders } from "shared/helpers/auth-tools";
import { getError } from "shared/helpers/get-error";

export const useMenuItems = () => {
    const [menuItems, setMenuItems] = useState<AppMenuItem[]>([]);

    useEffect(() => {
        const fetchMenu = async () => {
            try {
                const response = await fetch(MENU_API, {
                    headers: getAuthHeaders()
                });
                const data = await response.json();

                if (isArray(data) && !isEmpty(data)) {
                    setMenuItems(data);
                }
            } catch (error) {
                console.error(`Failed to fetch menu: ${getError(error)}`);;
            }
        };
        fetchMenu();
    }, []);

    return menuItems;
};
