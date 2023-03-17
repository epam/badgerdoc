import { colorDictionary } from '../../../constants/general';

const isValidHex = (hex: string) => /^#([A-Fa-f0-9]{3,4}){1,2}$/.test(hex);

const isValidHSL = (hslString: string): boolean => {
    const hslRegex = /^hsl\(\d{1,3},\s*\d{1,3}%,\s*\d{1,3}%\)$/i;
    return hslRegex.test(hslString);
};

const getChunksFromString = (st: string, chunkSize: number) =>
    st.match(new RegExp(`.{${chunkSize}}`, 'g'));

const convertHexUnitTo256 = (hexStr: string) => parseInt(hexStr.repeat(2 / hexStr.length), 16);

const getAlphaFloat = (a: number, alpha: number) => {
    if (typeof a !== 'undefined') {
        return a / 255;
    }
    if (alpha < 0 || alpha > 1) {
        return 1;
    }
    return alpha;
};

const hexToRGBA = (hex: string, alpha: number) => {
    const chunkSize = Math.floor((hex.length - 1) / 3);
    const hexArr = getChunksFromString(hex.slice(1), chunkSize);
    const [r, g, b, a] = hexArr!.map(convertHexUnitTo256);
    return `rgba(${r}, ${g}, ${b}, ${getAlphaFloat(a, alpha)})`;
};

const HSLToRGBA = (h: number, s: number, l: number, alpha: number) => {
    s /= 100;
    l /= 100;
    const k = (n: number) => (n + h / 30) % 12;
    const a = s * Math.min(l, 1 - l);
    const f = (n: number) => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
    return `rgba(${255 * f(0)}, ${255 * f(8)}, ${255 * f(4)}, ${alpha})`;
};

const extractHSLValues = (hslString: string): number[] => {
    const hslRegex = /hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/;
    const match = hslString.match(hslRegex);
    if (match) {
        const hslValues = [match[1], match[2], match[3]].map(Number);
        return hslValues;
    }
    return [];
};

export const stringToRGBA = (color: string, opacity: number) => {
    if (isValidHex(color)) {
        return hexToRGBA(color, opacity);
    }

    if (isValidHSL(color)) {
        const [h, s, l] = extractHSLValues(color);
        return HSLToRGBA(h, s, l, opacity);
    }
    if (colorDictionary[color]) {
        return `rgba(${colorDictionary[color].join(', ')}, ${opacity})`;
    }

    return '';
};
