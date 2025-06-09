import React, { createContext, useContext, useEffect, useState } from 'react';
import { Text as ErrorText } from '@epam/loveship';

import { useNotifications } from 'shared/components/notifications';
import { getAuthHeaders } from 'shared/helpers/auth-tools';
import { getError } from 'shared/helpers/get-error';

export interface AppMenuItem {
    name: string;
    url: string;
    is_external?: boolean;
    is_iframe?: boolean;
    iframe_url?: string;
    children?: AppMenuItem[];
}

interface AppMenuContextType {
    menuItems: AppMenuItem[];
    isLoading: boolean;
}

const AppMenuContext = createContext<AppMenuContextType>({
    menuItems: [],
    isLoading: false
});

export const AppMenuProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [menuItems, setMenuItems] = useState<AppMenuItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const { notifyError } = useNotifications();

    useEffect(() => {
        const fetchMenu = async () => {
            setIsLoading(true);
            try {
                const response = await fetch('http://demo.badgerdoc.com:8080/core/menu', {
                    headers: getAuthHeaders()
                });
                const data = await response.json();
                setMenuItems(data);
            } catch (error) {
                notifyError(<ErrorText>{getError(error)}</ErrorText>);
            } finally {
                setIsLoading(false);
            }
        };
        fetchMenu();
    }, [notifyError]);

    return (
        <AppMenuContext.Provider value={{ menuItems, isLoading }}>
            {children}
        </AppMenuContext.Provider>
    );
};

export const useAppMenu = () => useContext(AppMenuContext);
