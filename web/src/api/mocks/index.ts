import { datasets } from './datatsets';
import { documents } from './files';
import { jobById, jobs } from './jobs';
import { pipelines } from './pipelines';
import { users } from './users';
import { categories } from './categories';

import {
    PagedResponse,
    FileDocument,
    Dataset,
    Filter,
    Pipeline,
    Category,
    SearchBody,
    Operators,
    Taxon
} from '../typings';
import { tasks } from './tasks';
import { BadgerFetch, BadgerFetchBody, BadgerFetchProvider } from 'api/hooks/api';
import { annotations } from './annotations';
import { tokens } from './tokens';
import { models } from './models';
import { taxonomies } from './taxonomies';

const FILEMANAGEMENT_NAMESPACE = process.env.REACT_APP_FILEMANAGEMENT_API_NAMESPACE;
const JOBMANAGER_NAMESPACE = process.env.REACT_APP_JOBMANAGER_API_NAMESPACE;
const PIPELINEMANAGER_NAMESPACE = process.env.REACT_APP_PIPELINES_API_NAMESPACE;
const CATEGORIES_NAMESPACE = process.env.REACT_APP_CATEGORIES_API_NAMESPACE;
const USERS_NAMESPACE = process.env.REACT_APP_USERS_API_NAMESPACE;
const TOKENS_NAMESPACE = process.env.REACT_APP_TOKENS_API_NAMESPACE;
const MODELS_NAMESPACE = process.env.REACT_APP_MODELS_API_NAMESPACE;
const TAXONOMIES_NAMESPACE = process.env.REACT_APP_TAXONOMIES_API_NAMESPACE;

let datasetsMockData = datasets;
let jobsMockData = jobs;
let pipelinesMockData = pipelines;
let categoriesMockData = categories;
let usersMockData = users;
let tasksMockData = tasks;
let annotationsMockData = annotations;
let tokensMockData = tokens;
let modelsMockData = models;
let taxonomiesMockData = taxonomies;

const MOCKS: Record<string, Record<string, BadgerFetch<any>>> = {
    [`${FILEMANAGEMENT_NAMESPACE}/datasets/search`]: {
        post: async (): Promise<PagedResponse<Dataset>> => ({
            data: datasetsMockData,
            pagination: {
                page_num: 1,
                page_size: 100,
                total: datasetsMockData.length,
                has_more: false,
                min_pages_left: 1
            }
        })
    },
    [`${FILEMANAGEMENT_NAMESPACE}/datasets/bonds`]: {
        post: async (body) => {
            const bodyObj = JSON.parse(body as string);
            const dataset = datasetsMockData.find((dataset) => bodyObj.name === dataset.name);
            documents
                .filter((file) => bodyObj.objects.includes(file.id))
                .forEach((file) => file.datasets.push(String(dataset?.id)));
        }
    },
    [`${FILEMANAGEMENT_NAMESPACE}/datasets`]: {
        delete: async (body) => {
            const datasetName = JSON.parse(body as string).name;
            datasetsMockData = datasetsMockData.filter((dataset) => dataset.name !== datasetName);
        },
        post: async (body) => {
            datasetsMockData = [
                ...datasetsMockData,
                {
                    id: datasetsMockData.length + 1,
                    count: 0,
                    ...JSON.parse(body as string)
                }
            ];
        }
    },

    [`${JOBMANAGER_NAMESPACE}/jobs/search`]: {
        post: async () => ({
            data: jobsMockData,
            pagination: {
                total: jobsMockData.length
            }
        })
    },
    [`${JOBMANAGER_NAMESPACE}/jobs/create_job`]: {
        post: async (body) => {
            jobsMockData = [
                ...jobsMockData,
                {
                    id: (jobsMockData.length + 1).toString(),
                    ...JSON.parse(body as string)
                }
            ];
            return jobsMockData[jobsMockData.length - 1];
        }
    },
    [`${CATEGORIES_NAMESPACE}/tasks/search`]: {
        post: async () => ({
            data: tasksMockData,
            pagination: {
                total: tasksMockData.length
            }
        })
    },
    [`${CATEGORIES_NAMESPACE}/tasks`]: {
        post: async (body) => {
            const bodyObj = JSON.parse(body as string);
            return {
                pages: bodyObj.pages,
                is_validation: bodyObj.is_validation,
                file_id: bodyObj.file_id,
                user_id: bodyObj.user_id,
                deadline: bodyObj.deadline,
                job_id: bodyObj.job_id
            };
        }
    },
    [`${CATEGORIES_NAMESPACE}/tasks/1`]: {
        get: async () => tasksMockData[0]
    },
    [`${CATEGORIES_NAMESPACE}/tasks/3`]: {
        get: async () => tasksMockData[1]
    },
    [`${CATEGORIES_NAMESPACE}/tasks/3/pages_summary`]: {
        get: async () => {
            const validatedAnns = annotationsMockData.validated;
            const failedAnns = annotationsMockData.failed_validation_pages;
            const processed = [...validatedAnns, ...failedAnns];
            return {
                validated: validatedAnns,
                failed_validation_pages: failedAnns,
                annotated_pages: processed,
                not_processed: tasksMockData[2].pages.filter(
                    (pageNum) => !processed.includes(pageNum)
                )
            };
        }
    },
    [`${CATEGORIES_NAMESPACE}/annotation/3`]: {
        post: async (body) => {
            const bodyObj = JSON.parse(body as string);
            annotationsMockData = {
                ...annotationsMockData,
                failed_validation_pages: bodyObj.failed_validation_pages,
                validated: bodyObj.validated
            };
        }
    },
    [`${CATEGORIES_NAMESPACE}/tasks?job_id=1&pagination_page_size=15&pagination_start_page=1`]: {
        get: async () => {
            return {
                current_page: 1,
                page_size: 15,
                total_objects: tasksMockData.filter((task) => task.job.id === 1).length,
                annotation_tasks: tasksMockData.filter((task) => task.job.id === 1)
            };
        }
    },
    [`${CATEGORIES_NAMESPACE}/tasks/1/finish`]: {
        post: async () => (tasksMockData[0].status = 'Finished')
    },
    [`${CATEGORIES_NAMESPACE}/tasks/3/finish`]: {
        post: async () => (tasksMockData[2].status = 'Finished')
    },
    [`${JOBMANAGER_NAMESPACE}/jobs/1`]: {
        get: async () => jobById[0]
    },
    [`${JOBMANAGER_NAMESPACE}/jobs/3`]: {
        get: async () => jobById[1]
    },
    [`${CATEGORIES_NAMESPACE}/jobs/1/users`]: {
        get: async () => usersMockData
    },
    [`${CATEGORIES_NAMESPACE}/jobs/3/users`]: {
        get: async () => usersMockData
    },
    [`${CATEGORIES_NAMESPACE}/revisions/1/1`]: {
        get: async () => [
            {
                revision: annotationsMockData.revision,
                user: users[0].id,
                pipeline: null,
                date: '2022-01-31T11:48:42.092967',
                file_id: 1,
                job_id: 1,
                pages: {
                    '1': 'e3d0f54fde3378fb201afa8e343d219466053ca9'
                },
                validated: [],
                failed_validation_pages: [],
                tenant: 'test',
                task_id: 1
            }
        ]
    },
    [`${CATEGORIES_NAMESPACE}/annotation/1/1/revision-1`]: {
        get: async () => ({
            revision: annotationsMockData.revision,
            user: users[0].id,
            pipeline: null,
            date: '2022-02-03T07:54:12.177880',
            pages: annotationsMockData.pages,
            validated: annotationsMockData.validated,
            failed_validation_pages: annotationsMockData.failed_validation_pages
        })
    },
    [`${PIPELINEMANAGER_NAMESPACE}/pipeline`]: {
        post: async (body) => {
            const bodyObj: Partial<Pipeline> = JSON.parse(body as string);
            const id = pipelinesMockData.length + 1;
            pipelinesMockData = [
                ...pipelinesMockData,
                {
                    ...bodyObj,
                    id,
                    name: bodyObj.meta?.name
                } as Pipeline
            ];
            return { id };
        }
    },
    [`${PIPELINEMANAGER_NAMESPACE}/pipelines`]: {
        get: async () => pipelinesMockData
    },
    [`${PIPELINEMANAGER_NAMESPACE}/pipeline?name=pipeline1`]: {
        get: async () => pipelinesMockData[0]
    },
    [`${CATEGORIES_NAMESPACE}/categories/search`]: {
        post: async (body: BadgerFetchBody | undefined) => {
            const { filters, pagination } = JSON.parse(body as string) as SearchBody<Category>;
            let data = categoriesMockData;
            if (filters.length > 0) {
                const parentFilter = filters.find((filter) => filter.field === 'parent');
                const nameFilter = filters.find((filter) => filter.field === 'name');
                const nameFilterValue = String(nameFilter?.value ?? '').slice(1, -1);
                const typeFilter = filters.find((filter) => filter.field === 'type');
                const treeFilter = filters.find((filter) => filter.field === 'tree');

                if (treeFilter) {
                    data = data.filter((cat) => cat.parent === treeFilter.value);
                }
                if (parentFilter) {
                    data = data.filter((cat) => cat.parent === null);
                }
                if (nameFilterValue) {
                    data = data.filter((cat) => cat.name.includes(nameFilterValue));
                }
                if (typeFilter) {
                    data = data.filter((cat) => cat.type === typeFilter.value);
                }
                return {
                    data,
                    pagination
                };
            }
            return {
                data: categoriesMockData,
                pagination: {
                    page_num: 1,
                    page_size: 100
                }
            };
        }
    },
    [`${TAXONOMIES_NAMESPACE}/taxonomies/search`]: {
        post: async (body: BadgerFetchBody | undefined) => {
            const { filters, pagination } = JSON.parse(body as string) as SearchBody<Taxon>;
            let data = taxonomiesMockData;
            if (filters.length > 0) {
                const parentFilter = filters.find((filter) => filter.field === 'parent_id');
                const nameFilter = filters.find((filter) => filter.field === 'name');
                const nameFilterValue = String(nameFilter?.value ?? '').slice(1, -1);

                if (parentFilter) {
                    const value =
                        parentFilter.operator === Operators.IS_NULL ? null : parentFilter.value;

                    data = data.filter((taxon) => taxon.parent_id === value);
                }
                if (nameFilterValue) {
                    data = data.filter((taxon) => taxon.name.includes(nameFilterValue));
                }

                return {
                    data,
                    pagination
                };
            }
            return {
                data: taxonomiesMockData,
                pagination: {
                    page_num: 1,
                    page_size: 100
                }
            };
        }
    },
    [`${CATEGORIES_NAMESPACE}/jobs/1/categories/search`]: {
        post: async (body: BadgerFetchBody | undefined) => {
            const { filters, pagination } = JSON.parse(body as string) as SearchBody<Category>;
            let data = categoriesMockData;
            if (filters.length > 0) {
                const parentFilter = filters.find((filter) => filter.field === 'parent');
                const nameFilter = filters.find((filter) => filter.field === 'name');
                const nameFilterValue = String(nameFilter?.value ?? '').slice(1, -1);
                const typeFilter = filters.find((filter) => filter.field === 'type');
                const treeFilter = filters.find((filter) => filter.field === 'tree');

                if (treeFilter) {
                    data = data.filter((cat) => cat.parent === treeFilter.value);
                }
                if (parentFilter) {
                    data = data.filter((cat) => cat.parent === null);
                }
                if (nameFilterValue) {
                    data = data.filter((cat) => cat.name.includes(nameFilterValue));
                }
                if (typeFilter) {
                    data = data.filter((cat) => cat.type === typeFilter.value);
                }
                return {
                    data,
                    pagination
                };
            }
            return {
                data: categoriesMockData,
                pagination: {
                    page_num: 1,
                    page_size: 100
                }
            };
        }
    },
    [`${CATEGORIES_NAMESPACE}/jobs/3/categories`]: {
        get: async () => {
            return {
                data: [],
                pagination: {
                    page_num: 1,
                    page_size: 100
                }
            };
        }
    },
    [`${CATEGORIES_NAMESPACE}/categories`]: {
        post: async (body) => {
            categoriesMockData = [
                ...categoriesMockData,
                {
                    id: categoriesMockData.length + 1,
                    ...JSON.parse(body as string)
                }
            ];
        }
    },
    [`${CATEGORIES_NAMESPACE}/annotation/1/1/latest?page_numbers=1`]: {
        get: async () => annotationsMockData
    },
    [`${CATEGORIES_NAMESPACE}/annotation/1`]: {
        post: async (body) => {
            annotationsMockData = {
                ...annotationsMockData,
                ...JSON.parse(body as string)
            };
        }
    },
    [`${CATEGORIES_NAMESPACE}/annotation/3/1/latest?page_numbers=1`]: {
        get: async () => annotationsMockData
    },
    [`${CATEGORIES_NAMESPACE}/annotation/1`]: {
        post: async (body) => {
            annotationsMockData = {
                ...annotationsMockData,
                ...JSON.parse(body as string)
            };
        }
    },
    [`${CATEGORIES_NAMESPACE}/jobs?file_ids=1`]: {
        get: async () => {}
    },
    [`${TOKENS_NAMESPACE}/tokens/1?page_numbers=1`]: {
        get: async () => tokensMockData
    },
    [`${USERS_NAMESPACE}/token`]: {
        post: async () => {
            return {
                access_token:
                    'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJIY0dZYXVPeV9rN0tQLUpDdlJNUjd5b3BnV2pEc2lob2k0NW8zZElNQ0o0In0.eyJleHAiOjE2NDQ2MTgyMzYsImlhdCI6MTY0NDI1ODIzNiwianRpIjoiZDc1MDZkZDAtNjcwMC00OTYzLWI0NmMtY2ZlNWUxNDU3NjFjIiwiaXNzIjoiaHR0cDovL2RldjEuZ2Nvdi5ydS9hdXRoL3JlYWxtcy9tYXN0ZXIiLCJzdWIiOiIwMjMzNjY0Ni1mNWQwLTQ2NzAtYjExMS1jMTQwYTNhZDU4YjUiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhZG1pbi1jbGkiLCJzZXNzaW9uX3N0YXRlIjoiNDU1MTVhNDUtMmQzYy00MDJjLWI0MTgtNmI0YjkxNzNiMjM5IiwiYWNyIjoiMSIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJjcmVhdGUtcmVhbG0iLCJyb2xlLWFubm90YXRvciIsImFkbWluIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsibWFzdGVyLXJlYWxtIjp7InJvbGVzIjpbInZpZXctcmVhbG0iLCJ2aWV3LWlkZW50aXR5LXByb3ZpZGVycyIsIm1hbmFnZS1pZGVudGl0eS1wcm92aWRlcnMiLCJpbXBlcnNvbmF0aW9uIiwiY3JlYXRlLWNsaWVudCIsIm1hbmFnZS11c2VycyIsInF1ZXJ5LXJlYWxtcyIsInZpZXctYXV0aG9yaXphdGlvbiIsInF1ZXJ5LWNsaWVudHMiLCJxdWVyeS11c2VycyIsIm1hbmFnZS1ldmVudHMiLCJtYW5hZ2UtcmVhbG0iLCJ2aWV3LWV2ZW50cyIsInZpZXctdXNlcnMiLCJ2aWV3LWNsaWVudHMiLCJtYW5hZ2UtYXV0aG9yaXphdGlvbiIsIm1hbmFnZS1jbGllbnRzIiwicXVlcnktZ3JvdXBzIl19fSwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwic2lkIjoiNDU1MTVhNDUtMmQzYy00MDJjLWI0MTgtNmI0YjkxNzNiMjM5IiwidGVuYW50cyI6WyJ0ZXN0Il0sImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwicHJlZmVycmVkX3VzZXJuYW1lIjoiYWRtaW4ifQ.RBeaBP9uRjnBiMOQx4qjPEspkdkPzXxKuIvGcxehYwx_MfXr5Hi-FL5rYElghMLksZVIuPYNZQ8eJACMYqGEBG5rdM8ZDgmzq1Q0nNVSYy6GsItws4XkZmdX75EPUll1Esm6F28ao7HRTb-zR9lVLxy5CB9DRpu4kESxnHODur8caNBWSvTVa6tqyP_rGlgvKf1Hqr_fXR8ciOLWNnFp-hosyvBpaAicTTnv087xtGO2qSoEafVGZ19r0CF6EI2hjHJcqrx_zAndQADY4V-rA9m883Vk4JxF3L3aK1IRzsl5PyHFts2oDchdPiSxKS26Xh52f5BiHpX33XRvyoW6Yg',
                expires_in: 360000,
                refresh_expires_in: 1800,
                refresh_token:
                    'eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICIzOTZkZTVhOC0xNzU1LTQ2ODQtYjVlNS1kODU0OTRkN2JmYzIifQ.eyJleHAiOjE2NDQyNjAwMzYsImlhdCI6MTY0NDI1ODIzNiwianRpIjoiMzViOWRmOTQtNjcyNy00ZjI0LTk5MGUtMzkwYWVhZjE4YjQxIiwiaXNzIjoiaHR0cDovL2RldjEuZ2Nvdi5ydS9hdXRoL3JlYWxtcy9tYXN0ZXIiLCJhdWQiOiJodHRwOi8vZGV2MS5nY292LnJ1L2F1dGgvcmVhbG1zL21hc3RlciIsInN1YiI6IjAyMzM2NjQ2LWY1ZDAtNDY3MC1iMTExLWMxNDBhM2FkNThiNSIsInR5cCI6IlJlZnJlc2giLCJhenAiOiJhZG1pbi1jbGkiLCJzZXNzaW9uX3N0YXRlIjoiNDU1MTVhNDUtMmQzYy00MDJjLWI0MTgtNmI0YjkxNzNiMjM5Iiwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwic2lkIjoiNDU1MTVhNDUtMmQzYy00MDJjLWI0MTgtNmI0YjkxNzNiMjM5In0.qmbL47B4SqCXFg3IwKL-Iib_4WxrcqJefm5caXs-Y2E',
                token_type: 'Bearer',
                id_token: null,
                'not-before-policy': 0,
                session_state: '45515a45-2d3c-402c-b418-6b4b9173b239',
                scope: 'profile email'
            };
        }
    },
    [`${USERS_NAMESPACE}/users/current_v2`]: {
        get: async () => {
            return {
                exp: 1645816523,
                iat: 1645456523,
                jti: '78060755-7172-4f24-8dd0-3f9f4a26eeef',
                iss: 'http://dev1.gcov.ru/auth/realms/master',
                sub: '02336646-f5d0-4670-b111-c140a3ad58b5',
                typ: 'Bearer',
                azp: 'admin-cli',
                session_state: 'e33882a1-d719-4627-aa8d-9aabd3baaaa9',
                preferred_username: 'admin',
                email_verified: false,
                acr: '1',
                realm_access: {
                    roles: [
                        'create-realm',
                        'presenter',
                        'manager',
                        'role-annotator',
                        'admin',
                        'annotator',
                        'engineer'
                    ]
                },
                resource_access: {
                    'master-realm': {
                        roles: [
                            'view-realm',
                            'view-identity-providers',
                            'manage-identity-providers',
                            'impersonation',
                            'create-client',
                            'manage-users',
                            'query-realms',
                            'view-authorization',
                            'query-clients',
                            'query-users',
                            'manage-events',
                            'manage-realm',
                            'view-events',
                            'view-users',
                            'view-clients',
                            'manage-authorization',
                            'manage-clients',
                            'query-groups'
                        ]
                    }
                },
                scope: 'profile email',
                sid: 'e33882a1-d719-4627-aa8d-9aabd3baaaa9',
                tenants: ['test'],
                user_id: '02336646-f5d0-4670-b111-c140a3ad58b5',
                client_id: 'admin-cli',
                username: 'admin',
                active: true
            };
        }
    },
    [`${USERS_NAMESPACE}/users/current`]: {
        get: async () => {
            return {
                access: {
                    manageGroupMembership: true,
                    view: true,
                    mapRoles: true,
                    impersonate: true,
                    manage: true
                },
                attributes: {
                    tenants: ['test']
                },
                clientConsents: null,
                clientRoles: null,
                createdTimestamp: 1638362379072,
                credentials: null,
                disableableCredentialTypes: [],
                email: null,
                emailVerified: false,
                enabled: true,
                federatedIdentities: [],
                federationLink: null,
                firstName: null,
                groups: null,
                id: '02336646-f5d0-4670-b111-c140a3ad58b5',
                lastName: null,
                notBefore: 0,
                origin: null,
                realmRoles: null,
                requiredActions: [],
                self: null,
                serviceAccountClientId: null,
                username: 'admin'
            };
        }
    },
    [`${USERS_NAMESPACE}/users/current_v2`]: {
        get: async () => {
            return {
                exp: 1645816523,
                iat: 1645456523,
                jti: '78060755-7172-4f24-8dd0-3f9f4a26eeef',
                iss: 'http://dev1.gcov.ru/auth/realms/master',
                sub: '02336646-f5d0-4670-b111-c140a3ad58b5',
                typ: 'Bearer',
                azp: 'admin-cli',
                session_state: 'e33882a1-d719-4627-aa8d-9aabd3baaaa9',
                preferred_username: 'admin',
                email_verified: false,
                acr: '1',
                realm_access: {
                    roles: [
                        'create-realm',
                        'presenter',
                        'manager',
                        'role-annotator',
                        'admin',
                        'annotator',
                        'engineer'
                    ]
                },
                resource_access: {
                    'master-realm': {
                        roles: [
                            'view-realm',
                            'view-identity-providers',
                            'manage-identity-providers',
                            'impersonation',
                            'create-client',
                            'manage-users',
                            'query-realms',
                            'view-authorization',
                            'query-clients',
                            'query-users',
                            'manage-events',
                            'manage-realm',
                            'view-events',
                            'view-users',
                            'view-clients',
                            'manage-authorization',
                            'manage-clients',
                            'query-groups'
                        ]
                    }
                },
                scope: 'profile email',
                sid: 'e33882a1-d719-4627-aa8d-9aabd3baaaa9',
                tenants: ['test'],
                user_id: '02336646-f5d0-4670-b111-c140a3ad58b5',
                client_id: 'admin-cli',
                username: 'admin',
                active: true
            };
        }
    },
    [`${USERS_NAMESPACE}/users/search`]: {
        post: async () => usersMockData
    },

    [`${FILEMANAGEMENT_NAMESPACE}/files/search`]: {
        post: async (body) => {
            const datasetId = JSON.parse(body as string)?.filters?.find(
                (filter: Filter<keyof FileDocument>) => filter.field === 'datasets.id'
            )?.value;
            return {
                data: datasetId
                    ? documents.filter((file) => file.datasets.includes(datasetId.toString()))
                    : documents,
                pagination: {
                    page_num: 1,
                    page_size: 100,
                    total: documents.length,
                    has_more: false,
                    min_pages_left: 1
                }
            };
        }
    },

    [`${MODELS_NAMESPACE}/models/search`]: {
        post: async () => {
            return {
                data: modelsMockData,
                pagination: {
                    page_num: 1,
                    page_size: 100,
                    total: modelsMockData.length,
                    has_more: false,
                    min_pages_left: 1
                }
            };
        }
    }
};

const time = async (t: number) => new Promise((resolve) => setTimeout(() => resolve(null), t));

export const applyMocks = (fetchProvider: BadgerFetchProvider): BadgerFetchProvider => {
    // babel do not know Proxy yet
    // eslint-disable-next-line no-undef
    return new Proxy(fetchProvider, {
        apply(target, thisArg, argumentsList) {
            const [options] = argumentsList;
            const { url, method } = options;
            const mock = MOCKS[url]?.[method.toLowerCase()];
            if (mock) {
                return async function (body: any) {
                    await time(1000);

                    console.log(`MOCK: ${method.toUpperCase()} ${url}`);

                    return mock(body);
                };
            } else {
                console.warn('Mocks Allowed, but found missing mock: ', method?.toUpperCase(), url);
            }

            // @ts-ignore
            return Reflect.apply(target, thisArg, argumentsList);
        }
    });
};
