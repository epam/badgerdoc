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
    FlexSpacer,
    Burger,
    DropdownContainer
} from '@epam/loveship';
import { AdaptiveItemProps, MainMenuLogo } from '@epam/uui-components';
import { useHistory } from 'react-router-dom';
import { CurrentUser } from 'shared/contexts/current-user';
import { AppMenuItem } from 'api/typings';
import { clearAuthDetails } from 'shared/helpers/auth-tools';
import { useIsInIframe } from 'api/hooks/useIsInIframe';
import { DASHBOARD_PAGE, DOCUMENTS_PAGE, MY_DOCUMENTS_PAGE } from 'shared';

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
                return DOCUMENTS_PAGE;
            case isSimple:
                return MY_DOCUMENTS_PAGE;
            case isAnnotator:
                return DASHBOARD_PAGE;
            default:
                return DOCUMENTS_PAGE;
        }
    };

    const pathMatches = (path: string) => {
        return history.location.pathname.indexOf(path) === 0;
    };

    const getLinkTarget = (item: AppMenuItem) => {
        if (item.is_external) {
            return { target: '_blank', pathname: item.url };
        } else {
            return { pathname: item.badgerdoc_path };
        }
    };

    const renderAvatar = () =>
        currentUser && (
            <>
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
            </>
        );

    const renderMenuButton = (item: AppMenuItem, isDropdown?: boolean) => (
        <MainMenuButton
            key={item.name}
            caption={item.name}
            isLinkActive={pathMatches(item.badgerdoc_path)}
            link={getLinkTarget(item)}
            rawProps={{ 'data-page': item.badgerdoc_path }}
            estimatedWidth={145}
            onClick={() => isDropdown && close()}
            {...(item.is_external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
        />
    );

    const renderMenuItem = (item: AppMenuItem) => {
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
                    priority={menu.indexOf(item) + 1}
                    estimatedWidth={128}
                >
                    {item.children.map((child: AppMenuItem) => renderMenuButton(child, true))}
                </MainMenuDropdown>
            );
        }
        // Rendering a simple MainMenuButton
        return renderMenuButton(item);
    };
    const getMenuItems = (): AdaptiveItemProps<{ caption?: string; onClose?: () => void }>[] => {
        return [
            {
                id: 'burger',
                priority: 100,
                collapsedContainer: true,
                render: (param, hiddenItems) => (
                    <Burger
                        key={param.id}
                        renderBurgerContent={(param) => {
                            return (hiddenItems ?? [])
                                .filter((i) => i.id !== 'burger' && i.id !== 'logo')
                                .map((i) => i.render({ ...i, onClose: param.onClose }));
                        }}
                    />
                )
            },
            {
                id: 'logo',
                priority: 99,
                render: (param) => (
                    <MainMenuLogo key={param.id} href={getLogoLink()} logoUrl="/svg/logo.svg" />
                )
            },
            ...menu.map((item) => ({
                id: item.name,
                priority: menu.indexOf(item) + 1,
                render: () => renderMenuItem(item)
            })),
            {
                id: 'moreContainer',
                priority: 8,
                collapsedContainer: true,
                render: (param, hiddenItems) => (
                    <MainMenuDropdown caption="More" key={param.id}>
                        {hiddenItems?.map((i) => {
                            const item = menu.find((m) => m.name === i.id);
                            if (!item) return null;

                            if (item.children && item.children.length > 0) {
                                return (
                                    <Dropdown
                                        key={item.name}
                                        placement="right-start"
                                        renderTarget={(props) => (
                                            <DropdownMenuButton
                                                {...props}
                                                caption={item.name}
                                                isDropdown={true}
                                            />
                                        )}
                                        renderBody={(props) => (
                                            <DropdownContainer
                                                {...props}
                                                style={{ backgroundColor: '#303240' }}
                                            >
                                                {item?.children?.map((child) =>
                                                    renderMenuButton(child)
                                                )}
                                            </DropdownContainer>
                                        )}
                                    />
                                );
                            }
                            return renderMenuButton(item);
                        })}
                    </MainMenuDropdown>
                )
            },
            { id: 'flexSpacer', priority: 100, render: (param) => <FlexSpacer key={param.id} /> },
            {
                id: 'account',
                priority: 100,
                render: () => renderAvatar()
            }
        ];
    };
    if (isInIframe) return null;
    return (
        <FlexCell>
            <MainMenu items={getMenuItems()} />
        </FlexCell>
    );
};
