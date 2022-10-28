import { Category } from 'api/typings';
import React, { FC, useMemo } from 'react';
import { AnnotationRenderer, AnnotationsStyle, Annotation } from '../../typings';
import { scaleAnnotation } from '../../utils/scale-annotation';
import { defaultAnnotationRenderer } from './annotations-default-renderer';
import styles from './annotations-layer.module.scss';

export type AnnotationsLayerProps = {
    scale: number;
    annotations: Annotation[];
    renderAnnotation?: AnnotationRenderer;
    annotationsStyle?: AnnotationsStyle;
    categories?: Array<Category>;
    page: number;
    onAnnotationCopyPress: () => void;
    onAnnotationCutPress: () => void;
    onAnnotationPastePress: () => void;
    onAnnotationUndoPress: () => void;
    onAnnotationRedoPress: () => void;
};

export const AnnotationsLayer: FC<AnnotationsLayerProps> = ({
    children,
    scale,
    annotations,
    renderAnnotation = defaultAnnotationRenderer,
    page,
    onAnnotationCopyPress,
    onAnnotationCutPress,
    onAnnotationPastePress,
    onAnnotationUndoPress,
    onAnnotationRedoPress
}) => {
    const scaledAnnotations = useMemo(() => {
        return (annotations || []).map((a) => scaleAnnotation(a, scale));
    }, [annotations, scale]);

    return (
        <>
            <div className={`${styles.container} annotations`}>
                <div className={styles.children}>{children}</div>
                <div
                    className={styles.pano}
                    onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
                        if (e.ctrlKey && e.code === 'KeyC') {
                            onAnnotationCopyPress();
                        }
                        if (e.ctrlKey && e.code === 'KeyX') {
                            onAnnotationCutPress();
                        }
                        if (e.ctrlKey && e.code === 'KeyV') {
                            onAnnotationPastePress();
                        }
                        if (e.ctrlKey && e.code === 'KeyZ') {
                            onAnnotationUndoPress();
                        }
                        if (e.ctrlKey && e.code === 'KeyY') {
                            onAnnotationRedoPress();
                        }
                    }}
                    role="button"
                    tabIndex={0}
                >
                    {scaledAnnotations.map((annotation) =>
                        renderAnnotation({ annotation, scale, page })
                    )}
                </div>
            </div>
        </>
    );
};
