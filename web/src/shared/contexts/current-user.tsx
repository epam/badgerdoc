// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import React, { FC, useEffect, useMemo, useState } from 'react';
import { noop, uniq } from 'lodash';
import { User } from 'api/typings';
import { useMenuItems } from 'api/hooks/menu';
import { AppMenuItem } from 'api/typings';

type UserContext = {
    currentUser: User | null;
    setCurrentUser: React.Dispatch<React.SetStateAction<User | null>>;
    isEngineer: boolean;
    isAnnotator: boolean;
    isSimple: boolean;
    menu: AppMenuItem[];
    isPipelinesDisabled: boolean;
};

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
    const menuItems = useMenuItems();

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
                    {
                        name: 'Documents',
                        url: '/documents',
                        badgerdoc_path: '/documents',
                        is_external: false,
                        is_iframe: false,
                        children: null
                    },
                    {
                        name: 'Jobs',
                        url: '/jobs',
                        badgerdoc_path: '/jobs',
                        is_external: false,
                        is_iframe: false,
                        children: null
                    },
                    {
                        name: 'My Tasks',
                        url: '/my tasks',
                        badgerdoc_path: '/my tasks',
                        is_external: false,
                        is_iframe: false,
                        children: null
                    },
                    {
                        name: 'Categories',
                        url: '/categories',
                        badgerdoc_path: '/categories',
                        is_external: false,
                        is_iframe: false,
                        children: null
                    },
                    {
                        name: 'Reports',
                        url: '/reports',
                        badgerdoc_path: '/reports',
                        is_external: false,
                        is_iframe: false,
                        children: null
                    }
                ]);
                break;
            case isAnnotator:
                addItems([
                    {
                        name: 'My Tasks',
                        url: '/my tasks',
                        badgerdoc_path: '/my tasks',
                        is_external: false,
                        is_iframe: false,
                        children: null
                    }
                ]);
                break;
            case isSimple:
                addItems([
                    {
                        name: 'My Documents',
                        url: '/my documents',
                        badgerdoc_path: '/my documents',
                        is_external: false,
                        is_iframe: false,
                        children: null
                    }
                ]);
                break;
        }

        return uniq(items);
    }, [isEngineer, isAnnotator, isSimple]);

    const menu = menuItems ?? fallbackMenu;

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
