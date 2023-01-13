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
import capitalize from 'lodash/capitalize';
import { CurrentUser } from 'shared/contexts/current-user';
import { FlexSpacer } from '@epam/uui-components';
import { cloneDeep } from 'lodash';
import { clearAuthDetails } from 'shared/helpers/auth-tools';

export const AppHeader = () => {
    const history = useHistory();
    const { currentUser, setCurrentUser, menu, isSimple, isAnnotator, isEngineer } =
        useContext(CurrentUser);

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
    }, []);

    const getLogoLink = () => {
        switch (true) {
            case isEngineer:
                return '/documents';
            case isSimple:
                return '/my documents';
            case isAnnotator:
                return '/dashboard';
            default:
                return '/documents';
        }
    };

    return (
        <FlexCell>
            <MainMenu appLogoUrl="../svg/logo.svg" logoHref={getLogoLink()}>
                {menu.map((item) => {
                    const pathMatches = (path: string) => {
                        return history.location.pathname.indexOf(`/${path}`) === 0;
                    };

                    const renderMenuButton = (item: string) => {
                        return (
                            <MainMenuButton
                                isLinkActive={pathMatches(item)}
                                link={{ pathname: `/${item}` }}
                                rawProps={{
                                    'data-page': item
                                }}
                                key={item}
                                collapseToMore
                                caption={capitalize(item)}
                                priority={0}
                                estimatedWidth={145}
                            />
                        );
                    };

                    if (typeof item === 'object') {
                        const hasActiveChild =
                            item.items.findIndex((child) => pathMatches(child)) !== -1;
                        return (
                            <MainMenuDropdown
                                isLinkActive={hasActiveChild}
                                key={item.caption}
                                caption={item.caption}
                                priority={2}
                                estimatedWidth={128}
                            >
                                {item.items.map((innerItem: string) => renderMenuButton(innerItem))}
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
