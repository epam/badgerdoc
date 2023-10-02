// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { CSSProperties, FC } from 'react';
import { Rect } from '../../typings';

type BoxSelectionProps = {
    selectionRect: Rect;
    selectionStyle?: CSSProperties;
};

export const BoxSelection: FC<BoxSelectionProps> = ({ selectionRect, selectionStyle }) => {
    return (
        <>
            <div
                style={{
                    zIndex: 1,
                    position: 'absolute',
                    top: selectionRect.top,
                    left: selectionRect.left,
                    width: selectionRect.right - selectionRect.left,
                    height: selectionRect.bottom - selectionRect.top,
                    ...selectionStyle
                }}
            ></div>
        </>
    );
};
