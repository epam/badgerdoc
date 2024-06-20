import noop from 'lodash/noop';
import React, { RefObject } from 'react';
import { Annotation, Bound, Maybe } from '../../../typings';
import styles from './table-cell-layer.module.scss';
import { TextLabel } from '../../text-label';
import { Category } from '../../../../../../api/typings';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';

type TableCellProps = {
    label?: string;
    color?: string;
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
    const cellCategory = categories?.find((el) => el.name === category) ?? 'te-cell';
    const { setCurrentCell, setTabValue, setTableMode } = useTaskAnnotatorContext();

    const annStyle = {
        position: 'absolute' as 'absolute',
        left: x - tableBound.x,
        top: y - tableBound.y,
        width: width,
        height: height,
        //border: `2px ${color} solid`,
        color: category === 'te-cell' ? '#1940FF' : '#FF1c60', //TODO: TEST
        zIndex: isSelected ? 10 : 1,
        background: cellCategory === 'te-cell' ? 'transparent' : cellCategory?.metadata?.color, //TODO: TEST,
        opacity: 0
    };

    const handleCellClick = (e: any) => {
        onClick(e);
        const cellId = e.target.getAttribute('data-id');
        const cellText = e.target.getAttribute('data-text');
        setCurrentCell({
            id: cellId,
            text: cellText
        });
        setTabValue('Data');
        setTableMode(true);
    };

    return (
        <div
            role="button"
            onClick={handleCellClick}
            onDoubleClick={onDoubleClick}
            onContextMenu={onContextMenu}
            onKeyPress={handleCellClick}
            className="table-cell"
            style={annStyle}
            ref={annotationRef}
            data-id={cell.id}
            data-text={cell.text}
            tabIndex={0}
        >
            {cell.text}
            <TextLabel
                id={cell.id}
                color={color}
                className={styles['tableAnnotation-label']}
                label={label}
                onCloseIconClick={onCloseIconClick}
                isEditable={isEditable}
            />
        </div>
    );
};

export const TableCellLayer = ({
    table,
    cells,
    // todo: consider removal scale param
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    scale,
    categories
}: {
    table: Annotation;
    cells: Maybe<Annotation[]>;
    scale: number;
    categories: Maybe<Category[]>;
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
