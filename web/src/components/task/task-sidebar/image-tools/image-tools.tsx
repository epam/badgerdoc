// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import { AnnotationImageToolType } from '../../../../shared';
import React from 'react';
import { FlexRow, IconButton, Tooltip } from '@epam/loveship';

import { ReactComponent as penIcon } from '@epam/assets/icons/common/content-edit-12.svg';
import { ReactComponent as brushIcon } from '@epam/assets/icons/common/editor-format_bold-24.svg';
import { ReactComponent as wandIcon } from '@epam/assets/icons/common/table-swap-18.svg';
import { ReactComponent as eraserIcon } from '@epam/assets/icons/common/action-delete-24.svg';
import { ReactComponent as dextrIcon } from '@epam/assets/icons/common/radio-point-10.svg';
import { ReactComponent as maskrcnnIcon } from '@epam/assets/icons/common/file-cloud_download-24.svg';
import { ReactComponent as selectIcon } from '@epam/assets/icons/common/table-sort_asc-18.svg';

type ImageToolProps = {
    onSelectTool: (t: AnnotationImageToolType) => void;
    disabled: boolean;
};

export const ImageTools = ({ onSelectTool, disabled }: ImageToolProps) => {
    return (
        <FlexRow>
            <Tooltip content="Pen" placement="bottom">
                <IconButton
                    icon={penIcon}
                    onClick={() => onSelectTool('pen')}
                    isDisabled={disabled}
                />
            </Tooltip>
            <Tooltip content="Brush" placement="bottom">
                <IconButton
                    icon={brushIcon}
                    onClick={() => onSelectTool('brush')}
                    isDisabled={disabled}
                />
            </Tooltip>
            <Tooltip content="Wand" placement="bottom">
                <IconButton
                    icon={wandIcon}
                    onClick={() => onSelectTool('wand')}
                    isDisabled={disabled}
                />
            </Tooltip>
            <Tooltip content="Eraser" placement="bottom">
                <IconButton
                    icon={eraserIcon}
                    onClick={() => onSelectTool('eraser')}
                    isDisabled={disabled}
                />
            </Tooltip>
            <Tooltip content="DEXTR" placement="bottom">
                <IconButton
                    icon={dextrIcon}
                    onClick={() => onSelectTool('dextr')}
                    isDisabled={disabled}
                />
            </Tooltip>
            <Tooltip content="MaskRCNN" placement="bottom">
                <IconButton
                    icon={maskrcnnIcon}
                    onClick={() => onSelectTool('rectangle')}
                    isDisabled={disabled}
                />
            </Tooltip>
            <Tooltip content="Select" placement="bottom">
                <IconButton
                    icon={selectIcon}
                    onClick={() => onSelectTool('select')}
                    isDisabled={disabled}
                />
            </Tooltip>
        </FlexRow>
    );
};
