import { Point } from '../typings';

const MAX_CLICK_DISTANCE = 3;

const isClick = (start: Point, end: Point) => {
    const distance = Math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2);
    if (distance < MAX_CLICK_DISTANCE) return true;
    return false;
};

export default isClick;
