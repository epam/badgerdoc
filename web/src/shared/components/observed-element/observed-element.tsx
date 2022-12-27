import React, { useEffect, FC, useRef, useMemo } from 'react';

const useIntersectionThreshold = (
    rootElement: HTMLElement | null,
    observedElement: HTMLElement | null
): number => {
    return useMemo(() => {
        if (!rootElement || !observedElement) {
            return 1;
        }

        const rootRect = rootElement.getBoundingClientRect();
        const elementRect = observedElement.getBoundingClientRect();

        return Math.min(1, rootRect.height / 2 / elementRect.height);
    }, [rootElement, observedElement]);
};

interface ObservedElementProps {
    rootRef?: React.RefObject<HTMLDivElement>;
    onIntersect: () => void;
    disabled?: boolean;
    width?: number;
    height?: number | string;
    className?: string;
}

const ObservedElement: FC<ObservedElementProps> = ({
    children,
    rootRef,
    onIntersect,
    disabled,
    width,
    height,
    className
}) => {
    const elementRef = useRef<HTMLDivElement>(null);
    const threshold = useIntersectionThreshold(rootRef?.current ?? null, elementRef.current);

    useEffect(() => {
        if (!rootRef?.current || !elementRef.current || disabled) return;
        const element = elementRef.current;

        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    onIntersect();
                }
            },
            {
                root: rootRef.current,
                rootMargin: '0px',
                threshold
            }
        );
        observer.observe(element);
        return () => {
            observer.unobserve(element);
            observer.disconnect();
        };
    }, [threshold, disabled]);

    return (
        <div ref={elementRef} style={{ width, height }} className={className}>
            {children}
        </div>
    );
};
export default ObservedElement;
