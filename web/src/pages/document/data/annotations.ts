import { Annotation } from 'shared';

const annotations: Record<number, Annotation[]> = {
    1: [
        {
            id: 1,
            boundType: 'box',
            bound: {
                x: 50,
                y: 50,
                width: 200,
                height: 100
            },
            category: 3
        },
        {
            id: 2,
            boundType: 'box',
            bound: {
                x: 150,
                y: 150,
                width: 300,
                height: 200
            },
            category: 2
        }
    ]
};

export default annotations;
