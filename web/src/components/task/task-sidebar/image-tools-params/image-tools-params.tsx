// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { ReactComponent as infoIcon } from '@epam/assets/icons/common/notification-info-outline-18.svg';
import {
    AnnotationImageToolType,
    BrushToolParams,
    EraserToolParams,
    PaperToolParams,
    PenToolParams,
    WandToolParams
} from '../../../../shared';
import { FlexCell, FlexRow, IconContainer, NumericInput, Slider, Tooltip } from '@epam/loveship';
import styles from './image-tools-params.module.scss';

const capitalize = (str: string) => {
    return str.charAt(0).toUpperCase() + str.slice(1);
};

export const ImageToolsParams = ({
    selectedTool,
    onChangeToolParams,
    toolParams
}: {
    selectedTool: AnnotationImageToolType;
    onChangeToolParams: (
        newParams: PenToolParams | BrushToolParams | EraserToolParams | WandToolParams
    ) => void;
    toolParams: PaperToolParams;
}) => {
    const [renderValues, setRenderValues] = useState(toolParams.values);
    useEffect(() => {
        setRenderValues(toolParams.values);
    }, [JSON.stringify(toolParams.values)]);
    /* No parameters should be here */
    if (selectedTool === 'select' || selectedTool === 'pen') return <></>;

    /* Not implemented tools*/
    if (selectedTool === 'dextr' || selectedTool === 'rectangle') return <></>;

    return (
        <div className={styles['image-tools-params']}>
            <span>{capitalize(selectedTool)}</span>
            {renderValues ? (
                Object.entries(renderValues).map((el, index) => {
                    return (
                        <FlexCell key={index} width="100%">
                            <FlexRow rawProps={{ style: { justifyContent: 'space-between' } }}>
                                <p className={styles['image-tool-name']}>
                                    {capitalize(el[0])}
                                    <Tooltip content="Some information about selected param">
                                        <IconContainer icon={infoIcon} onClick={() => null} />
                                    </Tooltip>
                                </p>
                                <NumericInput
                                    value={el[1].value}
                                    onValueChange={(e) => {
                                        let newParams:
                                            | PenToolParams
                                            | BrushToolParams
                                            | EraserToolParams
                                            | WandToolParams = renderValues;
                                        (newParams as any)[el[0]].value = e; //TODO: We have no choice but any here I believe
                                        setRenderValues(newParams);
                                        onChangeToolParams(newParams);
                                    }}
                                    min={el[1].bounds.min}
                                    max={el[1].bounds.max}
                                />
                            </FlexRow>
                            <Slider
                                min={el[1].bounds.min}
                                max={el[1].bounds.max}
                                step={5}
                                splitAt={25}
                                value={el[1].value}
                                onValueChange={(e) => {
                                    let newParams:
                                        | PenToolParams
                                        | BrushToolParams
                                        | EraserToolParams
                                        | WandToolParams = renderValues;
                                    (newParams as any)[el[0]].value = e; //TODO: We have no choice but any here I believe
                                    setRenderValues(newParams);
                                    onChangeToolParams(newParams);
                                }}
                                cx={styles['sliderNumbers']}
                            />
                        </FlexCell>
                    );
                })
            ) : (
                <></>
            )}
        </div>
    );
};
