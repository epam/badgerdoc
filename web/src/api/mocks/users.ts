import { User } from 'api/typings';

export const users: User[] = [
    {
        id: '02336646-f5d0-4670-b111-c140a3ad58b5',
        sub: '02336646-f5d0-4670-b111-c140a3ad58b5',
        username: 'Ivan Ivanov',
        tenants: ['test'],
        realm_access: {
            roles: ['engineer']
        }
    },
    {
        id: '20',
        sub: '20',
        username: 'Test Testov',
        tenants: ['test'],
        realm_access: {
            roles: ['engineer']
        }
    },
    {
        id: '30',
        sub: '30',
        username: 'User User',
        tenants: ['test'],
        realm_access: {
            roles: ['engineer']
        }
    }
];
