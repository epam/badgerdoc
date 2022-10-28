import paper from 'paper';
import { PaperTool, PaperToolParams, WandToolParams } from '../../../typings';
import { defaultOnKeyDown } from '../utils';
// @ts-ignore
import MagicWand from 'magic-wand-tool/src/MagicWand'; //TODO: There are no known TS implementation of this lib

const getUInt8Image = (img: any) => {
    const canvas = document.createElement('canvas');
    canvas.width = img.width;
    canvas.height = img.height;
    const ctx = canvas.getContext('2d');
    ctx!.drawImage(img, 0, 0, canvas.width, canvas.height);
    return new Uint8Array(ctx!.getImageData(0, 0, img.width, img.height).data.buffer);
};

const flood = (imageData: any, x: any, y: any, thr: any, rad: number) => {
    if (imageData == null) return new paper.Path();

    const image = {
        data: getUInt8Image(imageData),
        width: imageData.width,
        height: imageData.height,
        bytes: 4
    };
    let mask = MagicWand.floodFill(image, x, y, thr);
    rad = rad < 1 ? 1 : Math.abs(rad);
    mask = MagicWand.gaussBlurOnlyBorder(mask, rad);
    const contours = MagicWand.traceContours(mask).filter((x: { inner: any }) => !x.inner);
    if (contours[0]) {
        let points = contours[0].points;
        points = points.map((pt: { x: number; y: number }) => ({
            x: pt.x,
            y: pt.y
        }));

        const polygon = new paper.Path(points);
        polygon.closed = true;
        return polygon;
    }
    return new paper.Path();
};

export const createMagicWandTool = ({
    onDeleteHandler,
    params
}: {
    onDeleteHandler: (id: number) => void;
    params: PaperToolParams;
}): PaperTool => {
    const curTool: PaperTool = {
        tool: new paper.Tool(),
        path: {} as paper.Path,
        cocoSegments: [],
        params: params
    };

    curTool.tool.onKeyDown = (event: paper.KeyEvent) => {
        defaultOnKeyDown(event, onDeleteHandler);
    };
    curTool.tool.onMouseDown = (event: paper.ToolEvent) => {
        const x = Math.round(event.point.x);
        const y = Math.round(event.point.y);
        const image = document.getElementById('image-annotation');
        curTool.path = flood(
            image,
            x,
            y,
            (curTool.params.values as WandToolParams).threshold.value,
            (curTool.params.values as WandToolParams).deviation.value
        );
    };
    return curTool;
};
