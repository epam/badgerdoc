import React from 'react';
import styles from '../table-annotation.module.scss';
import { GutterPart, Maybe, TableGutter, TableGutterMap } from '../../../typings';
import { getGutterLeft, getGutterTop, sumArrToIndex } from '../helpers';

type GuttersLayerParams = {
    gutters: TableGutterMap;
    selectedGutter: Maybe<TableGutter>;
    onMouseDownOnGutter: (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => void;
    isCellMode: boolean;
    color?: string;
};

type GutterParams = {
    gutter: TableGutter;
    onMouseDownHandler: any;
    selectedGutter: Maybe<TableGutter>;
    isCellMode: boolean;
    color?: string;
};

type GutterPartParams = {
    selectedGutter: Maybe<TableGutter>;
    gutter: TableGutter;
    gutterPart: GutterPart;
    index: number;
    isCellMode: boolean;
    color?: string;
};

const GutterPartComponent = ({
    selectedGutter,
    gutter,
    gutterPart,
    index,
    isCellMode,
    color
}: GutterPartParams) => {
    const partStyle = (part: GutterPart, partStart: number) => {
        return {
            width: gutter.type === 'vertical' ? gutter.draggableGutterWidth : part.length,
            height: gutter.type === 'vertical' ? part.length : gutter.draggableGutterWidth,
            left: (gutter.type === 'vertical' ? 0 : partStart) + 'px',
            top: (gutter.type === 'vertical' ? partStart : 0) + 'px',
            background: 'transparent',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center'
        };
    };

    const isSelectedGutter = (): boolean | undefined => {
        return selectedGutter && gutter.id === selectedGutter.id && !isCellMode;
    };

    return (
        <div
            key={index}
            style={partStyle(gutterPart, sumArrToIndex(gutter, index))}
            className={styles['gutter-' + gutter.type]}
        >
            <div
                className="gutter-core"
                style={{
                    background: gutterPart.visibility ? color : 'transparent',
                    height:
                        gutter.type === 'vertical'
                            ? '100%'
                            : isSelectedGutter()
                            ? gutter.visibleGutterWidth * 2
                            : gutter.visibleGutterWidth,
                    width:
                        gutter.type === 'horizontal'
                            ? '100%'
                            : isSelectedGutter()
                            ? gutter.visibleGutterWidth * 2
                            : gutter.visibleGutterWidth
                }}
            />
        </div>
    );
};

const Gutter = ({
    gutter,
    onMouseDownHandler,
    selectedGutter,
    isCellMode,
    color
}: GutterParams) => {
    const gutterStyle = {
        width: gutter.type === 'vertical' ? gutter.draggableGutterWidth : '100%',
        height: gutter.type === 'vertical' ? '100%' : gutter.draggableGutterWidth,
        left: getGutterLeft(gutter),
        top: getGutterTop(gutter),
        background: 'transparent',
        zIndex: 2
    };

    return (
        <div
            style={gutterStyle}
            className={styles[`gutter`]}
            role="button"
            tabIndex={0}
            onMouseDown={onMouseDownHandler}
        >
            {gutter.parts.map((el, index) => (
                <GutterPartComponent
                    selectedGutter={selectedGutter}
                    gutter={gutter}
                    gutterPart={el}
                    index={index}
                    key={index}
                    isCellMode={isCellMode}
                    color={color}
                />
            ))}
        </div>
    );
};

export const GuttersLayer = ({
    gutters,
    selectedGutter,
    onMouseDownOnGutter,
    isCellMode,
    color
}: GuttersLayerParams) => {
    return (
        <>
            {Object.values(gutters).map((el, index) => (
                <Gutter
                    gutter={el}
                    key={index}
                    onMouseDownHandler={onMouseDownOnGutter}
                    selectedGutter={selectedGutter}
                    isCellMode={isCellMode}
                    color={color}
                />
            ))}
        </>
    );
};
