import { stringToRGBA } from './string-to-rgba';

const opacity = 0.5;
// all colors are the same
const HEX = '#ff0000';
const HSL = 'hsl(0, 100%, 50%)';
const colorKeyWord = 'red';

const RGBa = 'rgba(255, 0, 0, 0.5)';

const emptyString = '';
const randomStr = 'qwdj80(@9';

describe('stringToRGBA', () => {
    describe('should return empty string, if received an invalid parameter as a color:', () => {
        it('empty string', () => {
            const result = stringToRGBA(emptyString, opacity);
            expect(result).toEqual(emptyString);
        });
        it('invalid string', () => {
            const result = stringToRGBA(randomStr, opacity);
            expect(result).toEqual(emptyString);
        });
    });

    describe('should return the correct color string in RGBa format,', () => {
        it('if valid HEX string received', () => {
            const result = stringToRGBA(HEX, opacity);
            expect(result).toEqual(RGBa);
        });

        it('if valid HSL string received', () => {
            const result = stringToRGBA(HSL, opacity);
            expect(result).toEqual(RGBa);
        });

        it('if valid color keyword string received', () => {
            const result = stringToRGBA(colorKeyWord, opacity);
            expect(result).toEqual(RGBa);
        });
    });
});
