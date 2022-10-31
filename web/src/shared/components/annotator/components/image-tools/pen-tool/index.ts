import paper from 'paper';
import { PaperTool, PaperToolParams, PenToolParams } from '../../../typings';
import { defaultOnKeyDown } from '../utils';

export const createPenTool = ({
    onDeleteHandler,
    params
}: {
    onDeleteHandler: (id: number) => void;
    params: PaperToolParams;
}): PaperTool => {
    const curTool: PaperTool = {
        tool: new paper.Tool(),
        path: {} as paper.Path, //TODO: ??
        cocoSegments: [],
        params: params
    };
    curTool.tool.onMouseDown = (event: paper.ToolEvent) => {
        curTool.path = new paper.Path();
        curTool.path.strokeWidth = 3;
        curTool.path.strokeColor = new paper.Color(0, 0, 0);
        curTool.path.add(event.point);
    };
    curTool.tool.onMouseDrag = (event: paper.ToolEvent) => {
        curTool.path.add(event.point);
    };
    curTool.tool.onKeyDown = (event: paper.KeyEvent) => {
        defaultOnKeyDown(event, onDeleteHandler);
    };
    curTool.tool.onMouseUp = () => {
        curTool.path.removeSegments();
    };
    return curTool;
};
