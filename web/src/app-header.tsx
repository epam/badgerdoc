// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare, react-hooks/exhaustive-deps, no-restricted-globals */
import React, { useContext, useMemo, useCallback } from 'react';
import {
    Dropdown,
    DropdownMenuBody,
    DropdownMenuButton,
    DropdownMenuSplitter,
    FlexCell,
    FlexRow,
    MainMenu,
    MainMenuAvatar,
    MainMenuButton,
    MainMenuCustomElement,
    MainMenuDropdown,
    Text
} from '@epam/loveship';
import { useHistory } from 'react-router-dom';
import startCase from 'lodash/startCase';
import { CurrentUser } from 'shared/contexts/current-user';
import { FlexSpacer } from '@epam/uui-components';
import { cloneDeep, isEmpty } from 'lodash';
import { clearAuthDetails } from 'shared/helpers/auth-tools';
import { useAppMenu } from 'shared/contexts/app-menu';

interface AppMenuItem {
    name: string;
    url: string;
    is_external?: boolean;
    is_iframe?: boolean;
    iframe_url?: string;
    children?: AppMenuItem[];
}

export const AppHeader = () => {
    const history = useHistory();
    const { currentUser, setCurrentUser, menu, isSimple, isAnnotator, isEngineer } =
        useContext(CurrentUser);
    const { menuItems } = useAppMenu();

    const navItems = isEmpty(menuItems) ? menu : menuItems;

    const avatarUrl: string = useMemo(
        () =>
            currentUser?.id
                ? `https://avatars.dicebear.com/api/avataaars/${currentUser.id}.svg?background=%23ffffff`
                : '',
        [currentUser?.id]
    );

    const setNewTenant = useCallback(
        (event) => {
            const tenant = event.currentTarget.dataset?.tenant;
            localStorage.setItem('tenant', tenant);
            const user = cloneDeep(currentUser);
            user!.current_tenant = tenant;
            setCurrentUser(user);
        },
        [currentUser]
    );

    const onLogOut = useCallback(() => {
        clearAuthDetails();
        setCurrentUser(null);
        location.reload();
        sessionStorage.removeItem('filters');
    }, []);

    const getLogoLink = () => {
        switch (true) {
            case isEngineer:
                return '/documents';
            case isSimple:
                return '/my documents';
            case isAnnotator:
                return '/my tasks';
            default:
                return '/documents';
        }
    };

    return (
        <FlexCell>
            <MainMenu appLogoUrl="/svg/logo.svg" logoHref={getLogoLink()}>
                {navItems.map((item) => {
                    const pathMatches = (path: string) => {
                        return history.location.pathname.indexOf(`/${path}`) === 0;
                    };

                    const getLinkTarget = (item: AppMenuItem) => {
                        if (item.is_external) {
                            return { pathname: item.url };
                        } else if (item.is_iframe) {
                            return { pathname: '/iframe', search: `?url=${item.iframe_url}` };
                        } else {
                            return { pathname: item.url };
                        }
                    };

                    const renderMenuButton = (item: AppMenuItem) => {
                        return (
                            <MainMenuButton
                                isLinkActive={pathMatches(item.url)}
                                link={getLinkTarget(item)}
                                key={item.name}
                                collapseToMore
                                caption={startCase(item.name)}
                                priority={0}
                                estimatedWidth={145}
                                rawProps={{
                                    'data-page': item.name
                                }}
                                {...(item.is_external
                                    ? { target: '_blank', rel: 'noopener noreferrer' }
                                    : {})}
                            />
                        );
                    };

                    if (typeof item === 'object' && item.children && item.children.length > 0) {
                        const hasActiveChild =
                            item.children?.findIndex((child) => pathMatches(child.name)) !== -1;
                        return (
                            <MainMenuDropdown
                                isLinkActive={hasActiveChild}
                                key={item.name}
                                caption={item.name}
                                priority={2}
                                estimatedWidth={128}
                            >
                                {item.children.map((innerItem: AppMenuItem) =>
                                    renderMenuButton(innerItem)
                                )}
                            </MainMenuDropdown>
                        );
                    } else {
                        return renderMenuButton(item);
                    }
                })}
                <FlexSpacer />
                {currentUser && (
                    <FlexRow spacing="18">
                        <Text color="white">{currentUser.current_tenant}</Text>|
                        <Text color="white">{currentUser.username}</Text>
                        <MainMenuCustomElement>
                            <Dropdown
                                renderTarget={(props) => (
                                    <MainMenuAvatar {...props} avatarUrl={avatarUrl} isDropdown />
                                )}
                                renderBody={() => (
                                    <DropdownMenuBody>
                                        {currentUser.tenants.map((tenant) => (
                                            <DropdownMenuButton
                                                rawProps={{ 'data-tenant': tenant }}
                                                caption={tenant}
                                                key={tenant}
                                                color="night"
                                                onClick={setNewTenant}
                                            />
                                        ))}
                                        <DropdownMenuSplitter />
                                        <DropdownMenuButton caption="Log out" onClick={onLogOut} />
                                    </DropdownMenuBody>
                                )}
                                placement="bottom-end"
                            />
                        </MainMenuCustomElement>
                    </FlexRow>
                )}
            </MainMenu>
        </FlexCell>
    );
};
