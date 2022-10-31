import { DocumentView } from 'api/typings';
import React, { FC } from 'react';

type DocumentsFilterListIconProps = {
    isActive: boolean;
    isDisable: boolean;
    onDocViewChange: (view: DocumentView) => void;
};

export const DocumentsFilterListIcon: FC<DocumentsFilterListIconProps> = ({
    isDisable,
    isActive,
    onDocViewChange
}) => {
    let color = isActive ? '#008ACE' : '#CED0DB';
    color = isDisable ? '#CED0DB' : color;
    return (
        <svg
            width="36"
            height="36"
            viewBox="0 0 36 36"
            fill="#FFFFFF"
            xmlns="http://www.w3.org/2000/svg"
            onClick={isDisable ? () => {} : () => onDocViewChange('table')}
            style={isDisable ? {} : { cursor: 'pointer' }}
        >
            <rect x="0.5" y="0.5" width="35" height="35" stroke={color} />
            <rect x="6" y="8" width="24" height="2" rx="1" fill={color} />
            <rect x="6" y="17" width="24" height="2" rx="1" fill={color} />
            <rect x="6" y="26" width="24" height="2" rx="1" fill={color} />
        </svg>
    );
};
