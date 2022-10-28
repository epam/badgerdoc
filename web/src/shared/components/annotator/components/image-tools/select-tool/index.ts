import paper from 'paper';
import { PaperTool } from '../../../typings';
import {
    defaultOnKeyDown,
    highlightAllAnnotationPaths,
    removeAllSelections,
    selectAllAnnotationPaths
} from '../utils';

export const createSelectTool = ({
    onDeleteHandler
}: {
    onDeleteHandler: (id: number) => void;
}): PaperTool => {
    const curTool: PaperTool = {
        tool: new paper.Tool(),
        path: {} as paper.Path,
        cocoSegments: [],
        params: {} as any
    };

    curTool.tool.onMouseMove = (event: paper.ToolEvent) => {
        paper.project.activeLayer.selected = false;
        for (let child of paper.project.activeLayer.children) {
            if (child.data.isSelected) child.selected = true;
        }
        if (event.item) {
            highlightAllAnnotationPaths(event.item);
        }
    };
    curTool.tool.onKeyDown = (event: paper.KeyEvent) => {
        defaultOnKeyDown(event, onDeleteHandler);
    };
    curTool.tool.onMouseDown = (event: paper.ToolEvent) => {
        removeAllSelections();
        if (event.item) {
            selectAllAnnotationPaths(event.item);
        }
    };
    return curTool;
};
