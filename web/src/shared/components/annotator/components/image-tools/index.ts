import { AnnotationImageToolType, Maybe, PaperTool, PaperToolParams } from '../../typings';
import { createPenTool } from './pen-tool';
import { createSelectTool } from './select-tool';
import { createBrushTool } from './brush-tool';
import { createEraserTool } from './eraser-tool';
import { createMagicWandTool } from './magic-wand-tool';

export const createImageTool = (
    toolName: AnnotationImageToolType,
    onDeleteHandler: any,
    params: PaperToolParams
): Maybe<PaperTool> => {
    switch (toolName) {
        case 'pen':
            return createPenTool({ onDeleteHandler, params });
        case 'brush':
            return createBrushTool({ onDeleteHandler, params });
        case 'eraser':
            return createEraserTool({ onDeleteHandler, params });
        case 'dextr':
            return createPenTool({ onDeleteHandler, params });
        case 'rectangle':
            return createPenTool({ onDeleteHandler, params });
        case 'wand':
            return createMagicWandTool({ onDeleteHandler, params });
        case 'select':
            return createSelectTool({ onDeleteHandler });
    }
};
