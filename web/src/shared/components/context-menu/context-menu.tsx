import { noop } from 'lodash';
import React, { ReactNode, useEffect, useLayoutEffect, useRef, useState } from 'react';
import styles from './context-menu.module.scss';

interface Props<MenuItemT> {
    menuItems?: MenuItemT[];
    renderMenuItem?: (menuItem: MenuItemT) => ReactNode;
    onMenuItemClick?: (menuItem: MenuItemT, data: any | null) => void;
    pageX?: number;
    pageY?: number;
    hidden?: boolean;
    data?: any | null;
}

const ContextMenu = <MenuItemT extends { id: string | number; name?: string; shortcut?: string }>({
    menuItems: items = [],
    onMenuItemClick = noop,
    renderMenuItem = (item) => item.name,
    pageX = 0,
    pageY = 0,
    hidden,
    data
}: Props<MenuItemT>) => {
    const contextMenuRef = useRef<HTMLDivElement>(null);
    const [top, setTop] = useState<number>();
    const [left, setLeft] = useState<number>();

    useLayoutEffect(() => {
        if (contextMenuRef.current) {
            const { width, height } = contextMenuRef.current.getBoundingClientRect();
            setTop(pageY + height >= window.innerHeight ? pageY - height : pageY);
            setLeft(pageX + width >= window.innerWidth ? pageX - width : pageX);
        }
    }, [hidden, pageX, pageY]);
    return (
        <div
            className={`${styles['context-menu']}`}
            ref={contextMenuRef}
            style={{ top, left }}
            hidden={hidden}
        >
            {items.map((item) => {
                return (
                    <div
                        key={item.id}
                        role="none"
                        onMouseDown={() => {
                            onMenuItemClick(item, data);
                        }}
                        className={styles.item}
                    >
                        <div className={styles.item__name}>{renderMenuItem(item)}</div>
                        <div className={styles.item__shortcut}>{item.shortcut}</div>
                    </div>
                );
            })}
        </div>
    );
};

export default ContextMenu;

export const useContextMenu = () => {
    const [hidden, setHidden] = useState(true);
    const [pageX, setPageX] = useState(0);
    const [pageY, setPageY] = useState(0);
    const [data, setData] = useState(null);

    useEffect(() => {
        if (!hidden) {
            const hideMenu = () => {
                setHidden(true);
            };
            document.addEventListener('mousedown', hideMenu);
            document.addEventListener('contextmenu', hideMenu);
            window.addEventListener('scroll', hideMenu, true);
            return () => {
                document.removeEventListener('mousedown', hideMenu);
                document.removeEventListener('contextmenu', hideMenu);
                window.removeEventListener('scroll', hideMenu, true);
            };
        }
    }, [hidden]);

    return {
        showMenu(event: React.MouseEvent, data: any | null) {
            setPageX(event.pageX);
            setPageY(event.pageY);
            setData(data);
            setHidden(false);
        },
        getMenuProps() {
            return {
                hidden,
                pageX,
                pageY,
                data
            };
        }
    };
};
