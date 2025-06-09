import React, { createContext, useContext, useEffect, useState } from 'react';
import { getAuthHeaders } from 'shared/helpers/auth-tools';

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
    error: string | null;
}

const AppMenuContext = createContext<AppMenuContextType>({
    menuItems: [],
    isLoading: false,
    error: null
});

export const AppMenuProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [menuItems, setMenuItems] = useState<AppMenuItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchMenu = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const response = await fetch('http://demo.badgerdoc.com:8080/core/menu', {
                    headers: getAuthHeaders()
                });
                const data = await response.json();
                setMenuItems(data);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };
        fetchMenu();
    }, []);

    return (
        <AppMenuContext.Provider value={{ menuItems, isLoading, error }}>
            {children}
        </AppMenuContext.Provider>
    );
};

export const useAppMenu = () => useContext(AppMenuContext);
