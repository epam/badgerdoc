// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare, react-hooks/exhaustive-deps, no-restricted-globals */
import React, { useContext, useMemo, useCallback } from 'react';
import { cloneDeep, isEmpty } from 'lodash';
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
    Text,
    FlexSpacer
} from '@epam/loveship';
import { useHistory } from 'react-router-dom';
import startCase from 'lodash/startCase';
import { CurrentUser } from 'shared/contexts/current-user';
import { AppMenuItem } from 'api/typings';
import { clearAuthDetails } from 'shared/helpers/auth-tools';
import { useIsInIframe } from 'api/hooks/iframe';

export const AppHeader = () => {
    const history = useHistory();
    const { currentUser, setCurrentUser, menu, isSimple, isAnnotator, isEngineer } =
        useContext(CurrentUser);
    const isInIframe = useIsInIframe();

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

    const pathMatches = (path: string) => {
        return history.location.pathname.indexOf(path) === 0;
    };

    const getLinkTarget = (item: AppMenuItem) => {
        if (item.is_iframe) {
            return { pathname: '/iframe', search: `?url=${item.url}` };
        } else {
            return { pathname: item.badgerdoc_path };
        }
    };

    const renderMenuButton = (item: AppMenuItem, isDropdown?: boolean) => (
        <MainMenuButton
            key={item.name}
            caption={startCase(item.name)}
            isLinkActive={pathMatches(item.badgerdoc_path)}
            link={getLinkTarget(item)}
            rawProps={{ 'data-page': item.badgerdoc_path }}
            collapseToMore
            priority={0}
            estimatedWidth={145}
            onClick={() => isDropdown && close()}
            {...(item.is_external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
        />
    );

    if (isInIframe) return null;
    return (
        <FlexCell>
            <MainMenu appLogoUrl="/svg/logo.svg" logoHref={getLogoLink()}>
                {menu.map((item) => {
                    // Check if there are children (nesting level 2 maximum)
                    if (item.children && !isEmpty(item.children)) {
                        // Rendering a Dropdown with Child Items
                        const hasActiveChild = item.children.some((child: AppMenuItem) =>
                            pathMatches(child.badgerdoc_path)
                        );
                        return (
                            <MainMenuDropdown
                                key={item.name}
                                caption={item.name}
                                isLinkActive={hasActiveChild}
                                priority={2}
                                estimatedWidth={128}
                            >
                                {item.children.map((child: AppMenuItem) =>
                                    renderMenuButton(child, true)
                                )}
                            </MainMenuDropdown>
                        );
                    }
                    // Rendering a simple MainMenuButton
                    return renderMenuButton(item);
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
