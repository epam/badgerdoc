import { createTextFromToken } from '../tokens';
import { PageToken } from 'shared';

describe('createTextFromToken', () => {
    const createToken = (tokenTextContent: {
        previous?: string;
        after?: string;
        text: string;
    }): PageToken => ({
        ...tokenTextContent,
        x: 0,
        y: 0,
        width: 0,
        height: 0
    });

    test('Must return text with "previous"/"after" symbols', () => {
        const token = createToken({
            previous: '.',
            after: ',',
            text: 'Text'
        });

        expect(createTextFromToken(token)).toBe('.Text,');
    });
    test('Must return text with "after" symbols', () => {
        const token = createToken({
            after: ',',
            text: 'Text'
        });

        expect(createTextFromToken(token)).toBe('Text,');
    });
    test('Must return text with "before" symbols', () => {
        const token = createToken({
            previous: '.',
            text: 'Text'
        });

        expect(createTextFromToken(token)).toBe('.Text');
    });
    test('Must return just text', () => {
        const token = createToken({
            text: 'Text'
        });

        expect(createTextFromToken(token)).toBe('Text');
    });
});
