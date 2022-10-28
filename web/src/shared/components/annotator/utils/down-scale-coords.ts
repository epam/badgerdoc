import { Point } from '../typings';

export const downScaleCoords = (coords: Point[], scale: number): Point[] => {
    return coords.map((p) => ({ x: p.x / scale, y: p.y / scale }));
};
