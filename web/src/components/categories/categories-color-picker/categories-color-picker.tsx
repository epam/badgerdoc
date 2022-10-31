import React, { useEffect, useState } from 'react';
import { IDropdownToggler } from '@epam/uui';
import { FlexRow, Panel, Button, Dropdown } from '@epam/loveship';
import { HexColorPicker } from 'react-colorful';
import styles from './categories-color-picker.module.scss';

type CategoriesColorPickerProps = {
    selectedColor(color: string): void;
    defaultColor: string;
};

export const CategoriesColorPicker: React.FC<CategoriesColorPickerProps> = ({
    selectedColor,
    defaultColor = '#313335'
}) => {
    const [color, setColor] = useState(defaultColor);

    useEffect(() => {
        selectedColor(color);
    }, [color]);

    const colorPickerView = () => {
        return (
            <Panel background="white" shadow={true}>
                <FlexRow padding="12" vPadding="12">
                    <HexColorPicker color={color} onChange={setColor} />
                </FlexRow>
            </Panel>
        );
    };

    return (
        <>
            <Dropdown
                renderBody={() => colorPickerView()}
                renderTarget={(props: IDropdownToggler) => (
                    <div className={styles['color-picker-panel']}>
                        <Button
                            caption="Choose a color"
                            {...props}
                            cx={styles['color-picker-panel_button']}
                        />{' '}
                        <div
                            className={styles['color-picker-panel_box']}
                            style={{ background: color }}
                        ></div>
                    </div>
                )}
            />
        </>
    );
};
