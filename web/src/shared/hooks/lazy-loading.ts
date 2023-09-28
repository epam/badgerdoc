// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import { useEffect, useMemo } from 'react';

export const useLazyLoading = (elementRef: any, containerRef: any, onScroll: () => void) => {
    const options = useMemo(
        () => ({
            rootMargin: '0px',
            root: containerRef.current
        }),
        [containerRef.current]
    );

    const observer = new IntersectionObserver((elements) => {
        if (elements[0].isIntersecting) {
            onScroll();
        }
    }, options);

    useEffect(() => {
        if (elementRef.current) {
            observer.observe(elementRef.current);
        }

        return () => {
            if (elementRef.current) {
                observer.unobserve(elementRef.current);
            }
        };
    }, [elementRef]);
};
