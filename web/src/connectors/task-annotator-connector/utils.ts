import { Category, Label } from 'api/typings';
import { Annotation, PaperToolParams, ToolNames } from 'shared';

export const getToolsParams = (
    selectedTool: ToolNames,
    storedParams: Record<ToolNames, PaperToolParams | undefined>
): PaperToolParams | undefined => {
    switch (selectedTool) {
        case 'eraser':
            if (storedParams.eraser) return storedParams.eraser;
            else
                return {
                    type: 'slider-number',
                    values: {
                        radius: { value: 40, bounds: { min: 0, max: 150 } }
                    }
                };
        case 'brush':
            if (storedParams.brush) return storedParams.brush;
            else
                return {
                    type: 'slider-number',
                    values: {
                        radius: { value: 40, bounds: { min: 0, max: 150 } }
                    }
                };
        case 'wand':
            if (storedParams.wand) return storedParams.wand;
            else
                return {
                    type: 'slider-number',
                    values: {
                        threshold: { value: 35, bounds: { min: 0, max: 150 } },
                        deviation: { value: 15, bounds: { min: 0, max: 150 } }
                    }
                };
        case 'dextr':
        case 'rectangle':
        case 'select':
        case 'pen':
            break;
    }
};

export const mapCategoriesIdToCategories = (ids: string[], categories: Category[]) =>
    ids.reduce((accumulator: Label[], id) => {
        const category = categories.find((item) => item.id === id);
        if (category) accumulator.push({ id, name: category.name });

        return accumulator;
    }, []);

export const removeAnnotationAndLabels = (
    annotations: Annotation[],
    annotationToRemove: Annotation
) =>
    annotations.reduce((accumulator: Annotation[], annotation) => {
        if (
            annotationToRemove &&
            annotationToRemove.children &&
            annotationToRemove.boundType === 'table' &&
            annotationToRemove.children.includes(annotation.id) &&
            annotation.boundType === 'table_cell'
        ) {
            return accumulator;
        }

        if (annotation.id === annotationToRemove.id) return accumulator;
        if (!annotation.labels?.length) {
            accumulator.push(annotation);
            return accumulator;
        }

        const currentLabels = [...annotation.labels];

        const labelIdxToDelete = currentLabels.findIndex(
            (item) => item.annotationId === annotationToRemove.id
        );
        if (labelIdxToDelete !== -1) {
            currentLabels.splice(labelIdxToDelete, 1);
        }

        accumulator.push({ ...annotation, labels: currentLabels });
        return accumulator;
    }, []);
