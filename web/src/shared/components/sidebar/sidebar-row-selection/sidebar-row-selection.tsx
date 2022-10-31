import React from 'react';
import styles from './sidebar-row-selection.module.scss';

type SidebarRowSelectionProps<T> = {
    children: React.ReactNode;
    entity: T;
    activeEntity?: T | null;
    onEntitySelect: (entity: T) => void;
    onMouseEnter?: () => void;
    onMouseLeave?: () => void;
};
export const SidebarRowSelection = <T extends { id: string | number }>({
    children,
    entity,
    activeEntity,
    onEntitySelect,
    onMouseEnter,
    onMouseLeave
}: SidebarRowSelectionProps<T>) => (
    <div
        key={entity.id}
        role="none"
        className={`${entity.id === activeEntity?.id ? styles.selected : styles.row}`}
        onClick={() => onEntitySelect(entity)}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
    >
        {children}
    </div>
);
