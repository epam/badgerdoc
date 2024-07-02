import noop from 'lodash/noop';
import React, { RefObject } from 'react';
import { Annotation, Bound, Maybe } from '../../../typings';
import { Category } from '../../../../../../api/typings';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';

type TableCellProps = {
    label?: string;
    color?: string;
    tableColor?: string;
    bound: Bound;
    cell: Annotation;
    tableBound: Bound;
    isSelected?: boolean;
    isEditable?: boolean;
    annotationRef?: RefObject<HTMLDivElement>;
    onClick?: React.MouseEventHandler<HTMLDivElement>;
    onDoubleClick?: React.MouseEventHandler<HTMLDivElement>;
    onContextMenu?: React.MouseEventHandler<HTMLDivElement>;
    onCloseIconClick?: React.MouseEventHandler<HTMLDivElement>;
    scale: number;
    category: Maybe<string | number>;
    categories: Maybe<Category[]>;
};

export const TableCell = ({
    label = '',
    color = 'black',
    tableColor,
    cell,
    bound,
    tableBound,
    isSelected,
    isEditable,
    annotationRef,
    onClick = noop,
    onDoubleClick = noop,
    onContextMenu = noop,
    onCloseIconClick = noop,
    category,
    categories
}: TableCellProps) => {
    const { x, y, width, height } = bound;
    const { setCurrentCell, setTabValue } = useTaskAnnotatorContext();

    const annStyle = {
        position: 'absolute' as 'absolute',
        left: x - tableBound.x,
        top: y - tableBound.y,
        width: x + width,
        height: y + height,
        //border: `2px ${color} solid`,
        color: category === 'te-cell' ? '#1940FF' : '#FF1c60', //TODO: TEST
        zIndex: isSelected ? 10 : 1,
        background: category === 'header_cell' ? tableColor : 'transparent',
        opacity: 0.2
    };

    const handleCellClick = (e: any) => {
        const cellId = e.target.getAttribute('data-id');
        const cellText = e.target.getAttribute('data-text');
        setCurrentCell({
            id: cellId,
            text: cellText
        });
        setTabValue('Data');
    };

    return (
        <div
            role="none"
            onClick={onClick}
            onDoubleClick={onDoubleClick}
            onContextMenu={onContextMenu}
            className="table-cell"
            style={annStyle}
            ref={annotationRef}
        >
            <div
                role="button"
                onClick={handleCellClick}
                onKeyPress={handleCellClick}
                tabIndex={0}
                style={{
                    width: x + width,
                    height: y + height,
                    opacity: 0,
                    cursor: 'pointer'
                }}
                data-id={cell.id}
                data-text={cell.text}
            ></div>
        </div>
    );
};

export const TableCellLayer = ({
    table,
    cells,
    // todo: consider removal scale param
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    scale,
    categories,
    tableColor
}: {
    table: Annotation;
    cells: Maybe<Annotation[]>;
    scale: number;
    categories: Maybe<Category[]>;
    tableColor?: string;
}) => {
    return cells ? (
        <>
            {cells.map((el) => (
                <TableCell
                    key={el.id}
                    cell={el}
                    bound={el.bound}
                    tableBound={table.bound}
                    color={el.color}
                    tableColor={tableColor}
                    scale={scale}
                    category={el.category}
                    categories={categories}
                />
            ))}
        </>
    ) : (
        <></>
    );
};
