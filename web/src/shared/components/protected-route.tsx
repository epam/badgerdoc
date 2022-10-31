import { Path } from 'history';
import React, { useContext } from 'react';
import { Redirect, Route, RouteProps } from 'react-router';
import { CurrentUser, SubMenu } from 'shared/contexts/current-user';
interface ProtectedRouteProps extends RouteProps {}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = (props) => {
    const { menu } = useContext(CurrentUser);
    if (!menu.length) return null;
    if (isPathAllowed(menu, props.path)) {
        return <Route {...props} />;
    }
    return <Redirect to={`/${menu[0]}`} />;
};

export const isPathAllowed = (
    menu: (string | SubMenu)[],
    path: Path | readonly Path[] | undefined
) => {
    const [currentPath] = Array.isArray(path) ? path : [path];
    const currentMenuItem = currentPath.replace(/^\//, '');
    const foundIndex = menu.findIndex((item) => {
        if (typeof item === 'string') {
            return item === currentMenuItem;
        }
        return item.items.findIndex((innerItem) => innerItem === currentMenuItem) !== -1;
    });
    return foundIndex !== -1;
};
