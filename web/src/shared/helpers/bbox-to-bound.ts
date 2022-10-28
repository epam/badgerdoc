import { Bound } from 'shared/components/annotator/typings';

export const bboxToBound = (bbox: number[], scale: number = 1): Bound => ({
    x: bbox[0] * scale,
    y: bbox[1] * scale,
    width: (bbox[2] - bbox[0]) * scale,
    height: (bbox[3] - bbox[1]) * scale
});
