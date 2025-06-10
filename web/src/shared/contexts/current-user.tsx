// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import React, { FC, useEffect, useMemo, useState } from 'react';
import { Text as ErrorText } from '@epam/loveship';
import { isArray, isEmpty, noop, uniq } from 'lodash';
import { User } from 'api/typings';
import { useNotifications } from 'shared/components/notifications';
import { getAuthHeaders } from 'shared/helpers/auth-tools';
import { getError } from 'shared/helpers/get-error';

type UserContext = {
    currentUser: User | null;
    setCurrentUser: React.Dispatch<React.SetStateAction<User | null>>;
    isEngineer: boolean;
    isAnnotator: boolean;
    isSimple: boolean;
    menu: AppMenuItem[];
    isPipelinesDisabled: boolean;
};

export interface AppMenuItem {
    name: string;
    url: string;
    is_external?: boolean;
    is_iframe?: boolean;
    iframe_url?: string;
    children?: AppMenuItem[];
}

const isPipelinesDisabled = process.env.REACT_APP_PIPELINES_DISABLED === 'true';

export const CurrentUser = React.createContext<UserContext>({
    currentUser: null,
    setCurrentUser: noop,
    isAnnotator: false,
    isEngineer: false,
    isSimple: false,
    menu: [],
    isPipelinesDisabled: isPipelinesDisabled
});

type UserRole = 'annotator' | 'engineer' | 'viewer' | 'simple_flow';

export const ML_MENU_ITEMS = ['pipelines', 'categories', 'models', 'basements', 'reports'].filter(
    (el) => {
        if (isPipelinesDisabled) {
            return el !== 'pipelines' && el !== 'models';
        } else return el;
    }
);

export const UserContextProvider: FC<{ currentUser: User | null }> = ({
    currentUser,
    children
}) => {
    const [rolesList, setRoleList] = useState<string[]>([]);
    const [fetchedMenuItems, setFetchedMenuItems] = useState<AppMenuItem[] | null>(null);
    const { notifyError } = useNotifications();

    const isUserInRole = (role: UserRole) => {
        return rolesList.includes(role);
    };

    useEffect(() => {
        if (currentUser && currentUser.realm_access?.roles) {
            setRoleList(currentUser.realm_access.roles);
        }
    }, [currentUser]);

    const isEngineer = isUserInRole('engineer');
    const isAnnotator = isUserInRole('annotator');
    const isSimple = isUserInRole('simple_flow');

    // Fetch dynamic menu items
    useEffect(() => {
        const fetchMenu = async () => {
            try {
                const response = await fetch('http://demo.badgerdoc.com:8080/core/menu', {
                    headers: getAuthHeaders()
                });
                const data = await response.json();
                if (Array.isArray(data) && data.length > 0) {
                    setFetchedMenuItems(data);
                }
            } catch (error) {
                notifyError(<ErrorText>{getError(error)}</ErrorText>);
            }
        };
        fetchMenu();
    }, [notifyError]);

    const fallbackMenu = useMemo(() => {
        const items: AppMenuItem[] = [];

        const addItems = (newItems: AppMenuItem[]) => {
            for (const item of newItems) {
                if (!items.some((i) => i.url === item.url)) {
                    items.push(item);
                }
            }
        };

        switch (true) {
            case isEngineer:
                addItems([
                    { name: 'Documents', url: '/documents' },
                    { name: 'Jobs', url: '/jobs' },
                    { name: 'My Tasks', url: '/my tasks' },
                    { name: 'Categories', url: '/categories' },
                    { name: 'Reports', url: '/reports' }
                ]);
                break;
            case isAnnotator:
                addItems([{ name: 'My Tasks', url: '/my tasks' }]);
                break;
            case isSimple:
                addItems([{ name: 'My Documents', url: '/my documents' }]);
                break;
        }

        return uniq(items);
    }, [isEngineer, isAnnotator, isSimple]);

    const menu =
        isArray(fetchedMenuItems) && !isEmpty(fetchedMenuItems) ? fetchedMenuItems : fallbackMenu;

    const value: UserContext = useMemo<UserContext>(() => {
        return {
            currentUser,
            setCurrentUser: noop,
            isAnnotator,
            isEngineer,
            isSimple,
            menu,
            isPipelinesDisabled
        };
    }, [currentUser, isAnnotator, isEngineer, menu]);
    return <CurrentUser.Provider value={value}> {children}</CurrentUser.Provider>;
};
