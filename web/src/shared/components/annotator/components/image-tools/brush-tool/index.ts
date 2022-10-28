import paper from 'paper';
import { BrushToolParams, PaperTool, PaperToolParams } from '../../../typings';
import { defaultOnKeyDown } from '../utils';

export const createBrushTool = ({
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
        selection: {} as paper.Path,
        params: params
    };
    const createBrush = (point?: paper.Point) => {
        return new paper.Path.Circle({
            strokeColor: new paper.Color(0, 0, 0),
            strokeWidth: 3,
            radius: (curTool.params.values as BrushToolParams).radius.value,
            center: point || undefined,
            data: { isBrushCircle: true },
            visible: false
        });
    };

    const moveBrush = (event: paper.ToolEvent) => {
        const canvas = document.getElementById('canvas');
        if (!Object.values(curTool.path).length) {
            curTool.path = createBrush(event.point);
        }
        curTool.path.visible = !(
            event.point.y > canvas!.clientHeight - 5 || event.point.x > canvas!.clientWidth - 5
        );
        curTool.path.bringToFront();
        curTool.path.position = event.point;
    };

    curTool.tool.onMouseMove = (event: paper.ToolEvent) => {
        moveBrush(event);
    };

    curTool.tool.onMouseDown = () => {
        curTool.selection = new paper.Path();
        curTool.selection.strokeWidth = 1;
        curTool.selection.strokeColor = new paper.Color(0, 0, 0);
        curTool.selection.data.isBrushSelection = true;
    };

    curTool.tool.onMouseDrag = (event: paper.ToolEvent) => {
        moveBrush(event);
        let newSelection = curTool.selection!.unite(curTool.path);

        curTool.selection!.remove();
        curTool.selection = newSelection as paper.Path;
    };

    curTool.tool.onMouseUp = () => {
        if (curTool.selection != null) {
            //curTool.selection.remove();
            curTool.selection = null as unknown as paper.Path;
        }
    };

    curTool.tool.onKeyDown = (event: paper.KeyEvent) => {
        defaultOnKeyDown(event, onDeleteHandler);
    };
    return curTool;
};
