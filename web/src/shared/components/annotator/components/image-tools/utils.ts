import paper from 'paper';

export const removeAllSelections = () => {
    paper.project.activeLayer.selected = false;
    const toDelete = [];
    for (let child of paper.project.activeLayer.children) {
        if (child.data.isBBox) toDelete.push(child);
        child.selected = false;
        if (child.data.isSelected) {
            child.data.isSelected = false;
        }
    }
    for (let d of toDelete) {
        d.remove();
    }
};

export const drawBBox = (item: paper.Item) => {
    const groupBounds = item.bounds;
    const bbox = new paper.Path.Rectangle(groupBounds);
    bbox.data.isBBox = true;
    bbox.strokeWidth = 3;
    // @ts-ignore //TODO: IGNORE
    bbox.strokeColor = new paper.Color(item.fillColor);
    bbox.strokeColor.alpha = 1;
};

export const highlightAllAnnotationPaths = (item: paper.Item): void => {
    item.selected = true;
    if (item.data.annotationId) {
        for (let child of paper.project.activeLayer.children) {
            if (child.data.annotationId === item.data.annotationId) {
                child.selected = true;
            }
        }
    }
};

export const deleteAllSelectedAnnotationPaths = (onDeleteHandler: (id: number) => void) => {
    const toDelete = [];
    let id;
    for (let child of paper.project.activeLayer.children) {
        if (child.data.isBBox || child.data.isSelected) {
            if (child.data.annotationId) id = child.data.annotationId;
            toDelete.push(child);
        }
    }
    for (let elem of toDelete) elem.remove();
    onDeleteHandler(id);
};

export const selectAllAnnotationPaths = (item: paper.Item) => {
    const toDrawBBox: paper.Item[] = [];
    item.selected = true;
    item.data.isSelected = true;
    if (item.data.annotationId) {
        for (let child of paper.project.activeLayer.children) {
            if (child.data.annotationId === item.data.annotationId) {
                toDrawBBox.push(child);
                child.selected = true;
                child.data.isSelected = true;
            }
        }
    }

    drawBBox(item);
};

export const defaultOnKeyDown = (event: paper.KeyEvent, onDeleteHandler: (id: number) => void) => {
    switch (event.key) {
        case 'escape':
            removeAllSelections();
            break;
        case 'delete':
            deleteAllSelectedAnnotationPaths(onDeleteHandler);
            break;
    }
};
