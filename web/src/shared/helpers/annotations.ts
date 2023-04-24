import { stringToRGBA } from 'shared/components/annotator/utils/string-to-rgba';
import { COLORS, IS_CONTRAST_COLOR } from 'shared/constants/colors';

export const isContrastColor = (color: string) => {
    if (color in IS_CONTRAST_COLOR) {
        return IS_CONTRAST_COLOR[color];
    }

    return true;
};

export const getAnnotationLabelColors = (color: string) => {
    if (!COLORS.includes(color)) {
        return {
            color,
            backgroundColor: stringToRGBA(color, 0.2)
        };
    }

    return {
        backgroundColor: color,
        color: IS_CONTRAST_COLOR[color] ? '#fff' : '#303240'
    };
};
