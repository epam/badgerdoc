import React from 'react';
import { IDropdownToggler, cx } from '@epam/uui';
import { Panel, Button, Dropdown } from '@epam/loveship';
import styles from './categories-color-picker.module.scss';
import { COLORS } from 'shared/constants/colors';

type CategoriesColorPickerProps = {
    value: string;
    isInvalid?: boolean;
    onValueChange(color: string): void;
};

export const CategoriesColorPicker: React.FC<CategoriesColorPickerProps> = ({
    value,
    isInvalid,
    onValueChange
}) => {
    const colorPickerView = () => {
        return (
            <Panel background="white" shadow cx={styles['color-list']}>
                {COLORS.map((color) => (
                    <div
                        key={color}
                        role="none"
                        onClick={() => onValueChange(color)}
                        className={styles['color-cell']}
                        style={{ backgroundColor: color }}
                    />
                ))}
            </Panel>
        );
    };

    return (
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
                        className={cx(
                            styles['color-picker-panel_box'],
                            isInvalid && styles.invalid
                        )}
                        style={{ background: value }}
                    ></div>
                </div>
            )}
        />
    );
};
