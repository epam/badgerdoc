import React, { useCallback, useEffect, useRef } from 'react';

interface SyncedContainerProps {
    className?: string;
    height?: number;
    width?: number;
}

export interface SyncScrollValue {
    SyncedContainer: React.FC<SyncedContainerProps>;
}

export default function useSyncScroll(): SyncScrollValue {
    const syncedElements = useRef(new Set<HTMLElement>());

    const handleScroll = useCallback((event: Event) => {
        const target = event.target as HTMLElement;
        const scrollLeft = target.scrollLeft;
        const scrollTop = target.scrollTop;

        for (const element of syncedElements.current) {
            if (element !== target) {
                element.scroll(scrollLeft, scrollTop);
            }
        }
    }, []);

    const syncScroll = useCallback((element: HTMLElement | null) => {
        if (!element) {
            return;
        }
        syncedElements.current.add(element);
        element.addEventListener('scroll', handleScroll);

        return () => {
            syncedElements.current.delete(element);
            element.removeEventListener('scroll', handleScroll);
        };
    }, []);

    const SyncedContainer = useCallback<React.FC<SyncedContainerProps>>(
        ({ children, className, height, width }) => {
            const ref = useRef<HTMLDivElement | null>(null);

            useEffect(() => syncScroll(ref.current), []);

            return (
                <div ref={ref} className={className} style={{ height, width }}>
                    {children}
                </div>
            );
        },
        []
    );

    return {
        SyncedContainer
    };
}
