import React, { useEffect, useState } from 'react';

interface Props {
    ref: React.RefObject<HTMLDivElement>;
}

export const useHeight = ({ ref }: Props) => {
    const [categoriesHeight, setCategoriesHeight] = useState(0);

    const observer = new ResizeObserver((entries) => {
        for (let entry of entries) {
            setCategoriesHeight(entry.contentRect.height);
        }
    });

    if (ref.current) {
        observer.observe(ref.current);
    }
    return categoriesHeight;
};
