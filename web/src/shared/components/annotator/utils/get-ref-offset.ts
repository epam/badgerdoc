import React from 'react';

export const getRefOffset = (ref: React.RefObject<HTMLDivElement>) => {
    let top = 0;
    let left = 0;

    if (ref.current) {
        ({ top, left } = ref.current.getBoundingClientRect());
    }

    return { offsetLeft: left, offsetTop: top };
};
