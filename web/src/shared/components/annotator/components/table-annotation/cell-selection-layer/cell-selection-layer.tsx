import React from 'react';
import { Bound } from '../../../typings';

type CellSelectionLayerParams = {
    selectionBounds: Bound | undefined;
};

export const CellSelectionLayer = ({ selectionBounds }: CellSelectionLayerParams) => {
    const selectionStyle = (b: Bound) => {
        return {
            position: 'absolute' as 'absolute', // That's weird
            left: b.x,
            top: b.y,
            width: b.width,
            height: b.height,
            background: '#add8e6'
        };
    };
    return selectionBounds ? (
        <div style={selectionStyle(selectionBounds)} className="selectionBounds" />
    ) : (
        <></>
    );
};
