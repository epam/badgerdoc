import React, { useCallback, useEffect, useMemo, useRef } from 'react';

interface SyncedContainerProps {
    className?: string;
}

export interface SyncScrollValue {
    SyncedContainer: React.FC<SyncedContainerProps>;
}

export default function useSycnScroll(): SyncScrollValue {
    const syncedElements = useMemo(() => new Set<HTMLElement>(), []);

    const handleScroll = useCallback((event: Event) => {
        const target = event.target as HTMLElement;
        const scrollLeft = target.scrollLeft;
        const scrollTop = target.scrollTop;

        for (const element of syncedElements) {
            if (element !== target) {
                element.scroll(scrollLeft, scrollTop);
            }
        }
    }, []);

    const syncScroll = useCallback((element: HTMLElement | null) => {
        if (!element) {
            return;
        }
        syncedElements.add(element);
        element.addEventListener('scroll', handleScroll);

        return () => {
            syncedElements.delete(element);
            element.removeEventListener('scroll', handleScroll);
        };
    }, []);

    const SyncedContainer = useCallback<React.FC<SyncedContainerProps>>(
        ({ children, className }) => {
            const ref = useRef<HTMLDivElement | null>(null);

            useEffect(() => syncScroll(ref.current), []);

            return (
                <div ref={ref} className={className}>
                    {children}
                </div>
            );
        },
        []
    );

    return useMemo(
        () => ({
            SyncedContainer
        }),
        []
    );
}
