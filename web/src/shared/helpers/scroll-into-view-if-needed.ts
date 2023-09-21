const isPointInsideRect = (point: { x: number; y: number }, rect: DOMRect): boolean => {
    return (
        point.x >= rect.left &&
        point.x <= rect.right &&
        point.y >= rect.top &&
        point.y <= rect.bottom
    );
};

const isRectIsFullyInAnotherRect = (rectIn: DOMRect, rectOut: DOMRect): boolean => {
    return (
        isPointInsideRect({ x: rectIn.left, y: rectIn.top }, rectOut) &&
        isPointInsideRect({ x: rectIn.right, y: rectIn.top }, rectOut) &&
        isPointInsideRect({ x: rectIn.right, y: rectIn.bottom }, rectOut) &&
        isPointInsideRect({ x: rectIn.left, y: rectIn.bottom }, rectOut)
    );
};

/**
 * Scrolls [childElement] into the visible area of [parentElement] if it's
 * not already within the visible area of the browser window.
 * @param parentElement
 * @param childElement
 */
export const scrollIntoViewIfNeeded = (parentElement: Element, childElement: Element) => {
    const isVisible = isRectIsFullyInAnotherRect(
        childElement.getBoundingClientRect(),
        parentElement.getBoundingClientRect()
    );

    if (!isVisible) {
        childElement.scrollIntoView();
    }
};
