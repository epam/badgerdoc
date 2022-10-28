import { Annotation } from '../typings';

export const scaleAnnotation = (annotation: Annotation, scale: number): Annotation => {
    const bound = {
        x: annotation.bound.x * scale,
        y: annotation.bound.y * scale,
        width: annotation.bound.width * scale,
        height: annotation.bound.height * scale
    };

    if (annotation.boundType === 'table' && annotation.table) {
        const tableRows = annotation.table.rows;
        const tableCols = annotation.table.cols;
        return {
            ...annotation,
            bound,
            table: {
                rows: tableRows.map((el) => el * scale),
                cols: tableCols.map((el) => el * scale)
            },
            tableCells: annotation.tableCells?.map((el) => scaleAnnotation(el, scale))
        };
    }

    return { ...annotation, bound };
};
