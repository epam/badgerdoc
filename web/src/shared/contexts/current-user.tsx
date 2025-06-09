// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import React, { FC, useEffect, useMemo, useState } from 'react';
import { User } from 'api/typings';
import { noop, uniq } from 'lodash';
import { AppMenuItem } from './app-menu';

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

    const menu = useMemo(() => {
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
            default:
                break;
        }

        return uniq(items);
    }, [isEngineer, isAnnotator, isSimple]);

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
