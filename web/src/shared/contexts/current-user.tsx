import React, { FC, useEffect, useMemo, useState } from 'react';
import { User } from 'api/typings';
import { noop, uniq } from 'lodash';

type UserContext = {
    currentUser: User | null;
    setCurrentUser: React.Dispatch<React.SetStateAction<User | null>>;
    isEngineer: boolean;
    isAnnotator: boolean;
    isSimple: boolean;
    menu: (string | SubMenu)[];
};

export const CurrentUser = React.createContext<UserContext>({
    currentUser: null,
    setCurrentUser: noop,
    isAnnotator: false,
    isEngineer: false,
    isSimple: false,
    menu: []
});

export type SubMenu = {
    caption: string;
    items: string[];
};

type UserRole = 'annotator' | 'engineer' | 'viewer' | 'simple_flow';

export const ML_MENU_ITEMS = ['pipelines', 'categories', 'models', 'basements'];

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
        const menu: (string | SubMenu)[] = [];
        switch (true) {
            case isEngineer:
                menu.push('documents', 'extractions', 'dashboard', {
                    caption: 'ML Management',
                    items: ML_MENU_ITEMS
                });
                break;
            case isAnnotator:
                menu.push('dashboard');
                break;
            case isSimple:
                menu.push('my documents');
                break;
            default:
                break;
        }
        return uniq(menu);
    }, [isEngineer, isAnnotator, isSimple]);

    const value: UserContext = useMemo<UserContext>(() => {
        return {
            currentUser,
            setCurrentUser: noop,
            isAnnotator,
            isEngineer,
            isSimple,
            menu
        };
    }, [currentUser, isAnnotator, isEngineer, menu]);
    return <CurrentUser.Provider value={value}> {children}</CurrentUser.Provider>;
};
