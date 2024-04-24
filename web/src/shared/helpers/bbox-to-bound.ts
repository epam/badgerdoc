import { Bound } from 'shared/components/annotator/typings';

export const bboxToBound = (bbox: number[], scale: number = 1): Bound => {
    if (!bbox) {
        return {
            x: 0,
            y: 0,
            width: 0,
            height: 0
        }
    }
    return {
        x: bbox[0] * scale,
        y: bbox[1] * scale,
        width: (bbox[2] - bbox[0]) * scale,
        height: (bbox[3] - bbox[1]) * scale
    }
}
