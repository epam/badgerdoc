import { Details } from './schemas';

export class ApiError extends Error {
    constructor(message: string, public summary: string, public details: Details) {
        super(message);
    }
}
