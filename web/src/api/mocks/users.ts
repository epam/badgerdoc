import { User } from 'api/typings';

export const users: User[] = [
    {
        id: '02336646-f5d0-4670-b111-c140a3ad58b5',
        user_id: '02336646-f5d0-4670-b111-c140a3ad58b5',
        username: 'Ivan Ivanov',
        tenants: ['test'],
        realm_access: {
            roles: ['engineer']
        }
    },
    {
        id: '20',
        user_id: '20',
        username: 'Test Testov',
        tenants: ['test'],
        realm_access: {
            roles: ['engineer']
        }
    },
    {
        id: '30',
        user_id: '30',
        username: 'User User',
        tenants: ['test'],
        realm_access: {
            roles: ['engineer']
        }
    }
];
