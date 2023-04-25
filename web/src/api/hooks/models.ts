import {
    Basement,
    Model,
    ModelDeployment,
    MutationHookType,
    Operators,
    PagedResponse,
    QueryHookType,
    SearchBody,
    Sorting,
    SortingDirection,
    Training,
    FilterWithDocumentExtraOption
} from 'api/typings';
import { useBadgerFetch } from './api';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { pageSizes } from '../../shared';
import { getError } from '../../shared/helpers/get-error';

const namespace = process.env.REACT_APP_MODELS_API_NAMESPACE;
const preprocessingNamespace = process.env.REACT_APP_TOKENS_API_NAMESPACE;
type UseModelsParamsType = {
    page: number;
    size: number;
    searchText: string;
    userId?: string | null;
    sortConfig: Sorting<keyof Model>;
    filters: Array<FilterWithDocumentExtraOption<keyof Model>>;
};

export function runPreprocessing(
    file_ids: Array<number>,
    pipeline_id: number,
    languages?: string[]
): Promise<string> {
    const body = languages?.length
        ? JSON.stringify({ file_ids, pipeline_id, languages })
        : JSON.stringify({ file_ids, pipeline_id });
    return useBadgerFetch<string>({
        url: `${preprocessingNamespace}/run_preprocess`,
        method: 'post'
    })(body);
}

export function addModel(data: Model): Promise<Model> {
    return useBadgerFetch<Model>({
        url: `${namespace}/models/create`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(data));
}

export function deployModel(id: string): Promise<{ [key: string]: string }> {
    const body = {
        id
    };
    return useBadgerFetch<{ [key: string]: string }>({
        url: `${namespace}/models/deploy`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}

export function editModel(data: Model): Promise<Model> {
    const body = { ...data };
    // TODO: replace this hardcode with real data (update UI issue 572)
    body.description = 'New model';
    return useBadgerFetch<Model>({
        url: `${namespace}/models/update`,
        method: 'put',
        withCredentials: true
    })(JSON.stringify(body));
}

export const useEditModelMutation: MutationHookType<Model, Model> = () => {
    const queryClient = useQueryClient();

    return useMutation(editModel, {
        onSuccess: () => {
            queryClient.invalidateQueries('models');
        }
    });
};

function undeployModel(id: string): Promise<{ [key: string]: string }> {
    const body = {
        id
    };
    return useBadgerFetch<{ [key: string]: string }>({
        url: `${namespace}/models/undeploy`,
        method: 'delete',
        withCredentials: true
    })(JSON.stringify(body));
}

function deleteUndeployedModel(id: string): Promise<{ [key: string]: string }> {
    const body = {
        id
    };
    return useBadgerFetch<{ [key: string]: string }>({
        url: `${namespace}/models/delete`,
        method: 'delete',
        withCredentials: true
    })(JSON.stringify(body));
}

export async function undeployAndDeleteModel(id: string): Promise<void> {
    try {
        await undeployModel(id);
        await deleteUndeployedModel(id);
    } catch (error) {
        console.error(`Failed to undeploy model: ${getError(error)}`);
    }
}

export const useAddModelMutation: MutationHookType<Model, Model> = () => {
    const queryClient = useQueryClient();

    return useMutation(addModel, {
        onSuccess: () => {
            queryClient.invalidateQueries('models');
        }
    });
};

export async function deployedPreprocessorsFetcher(
    page = 1,
    size = pageSizes._15,
    search: string = ''
): Promise<PagedResponse<Model>> {
    const filters = [
        { field: 'type', operator: Operators.EQ, value: 'preprocessing' },
        { field: 'status', operator: Operators.EQ, value: 'deployed' }
    ];
    if (search) {
        filters.push({
            field: 'name',
            operator: Operators.ILIKE,
            value: `%${search.trim().toLowerCase()}%`
        });
    }
    const body = {
        pagination: { page_num: page, page_size: size },
        filters,
        sorting: [{ direction: SortingDirection.ASC, field: 'name' }]
    };

    return useBadgerFetch<PagedResponse<Model>>({
        url: `${namespace}/models/search`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}

export const useModels: QueryHookType<UseModelsParamsType, PagedResponse<Model>> = (
    { page, size, searchText, sortConfig, filters },
    options
) => {
    return useQuery(
        ['models', page, size, searchText, sortConfig],
        async () => modelsFetcher(page, size, searchText, sortConfig, filters),
        options
    );
};

function modelsFetcher(
    page = 1,
    size = pageSizes._15,
    searchText?: string | null,
    sortConfig: {
        field: keyof Model;
        direction: SortingDirection;
    } = {
        field: 'name',
        direction: SortingDirection.ASC
    },
    filters: FilterWithDocumentExtraOption<keyof Model>[] = []
): Promise<PagedResponse<Model>> {
    if (searchText) {
        filters.push({
            field: 'name',
            operator: Operators.ILIKE,
            value: `%${searchText.trim().toLowerCase()}%`
        });
    }
    const body: SearchBody<Model> = {
        pagination: { page_num: page, page_size: size },
        filters,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field }]
    };

    return useBadgerFetch<PagedResponse<Model>>({
        url: `${namespace}/models/search`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}

type ModelByIdParams = {
    modelId: string;
    modelVer?: number;
};

export const useModelById: QueryHookType<ModelByIdParams, Model> = (
    { modelId, modelVer },
    options
) => {
    return useQuery(
        ['modelDetailed', modelId],
        () =>
            useBadgerFetch<Model>({
                url: `${namespace}/models/${
                    modelVer ? `${modelId}/${modelVer}` : `${modelId}?model_id=${modelId}`
                }`,
                method: 'get',
                withCredentials: true
            })(),
        options
    );
};

type ModelTrainingParams = {
    trainingId: number;
};

export const useModelTraining: QueryHookType<ModelTrainingParams, Training> = (
    { trainingId },
    options
) => {
    return useQuery(
        ['modelTraining', trainingId],
        () =>
            useBadgerFetch<Training>({
                url: `${namespace}/trainings/${trainingId}?training_id=${trainingId}`,
                method: 'get',
                withCredentials: true
            })(),
        options
    );
};

type ModelDeploymentParams = {
    modelName: string;
};

export const useModelDeployment: QueryHookType<ModelDeploymentParams, ModelDeployment> = (
    { modelName },
    options
) => {
    return useQuery(
        ['modelDeployment', modelName],
        () =>
            useBadgerFetch<ModelDeployment>({
                url: `${namespace}/deployed_models/${modelName}`,
                method: 'get',
                withCredentials: true
            })(),
        options
    );
};

type UseBasementParamsType = {
    page: number;
    size: number;
    searchText: string;
    userId?: string | null;
    sortConfig: Sorting<keyof Basement>;
    filters: Array<FilterWithDocumentExtraOption<keyof Basement>>;
};
export const useBasements: QueryHookType<UseBasementParamsType, PagedResponse<Basement>> = (
    { page, size, searchText, sortConfig, filters },
    options
) => {
    return useQuery(
        ['basements', page, size, searchText, sortConfig],
        async () => basementsFetcher(page, size, searchText, sortConfig, filters),
        options
    );
};

function basementsFetcher(
    page = 1,
    size = pageSizes._15,
    searchText?: string | null,
    sortConfig: {
        field: keyof Basement;
        direction: SortingDirection;
    } = {
        field: 'name',
        direction: SortingDirection.ASC
    },
    filters: FilterWithDocumentExtraOption<keyof Basement>[] = []
): Promise<PagedResponse<Basement>> {
    if (searchText) {
        filters.push({
            field: 'name',
            operator: Operators.ILIKE,
            value: `%${searchText.trim().toLowerCase()}%`
        });
    }
    const body: SearchBody<Basement> = {
        pagination: { page_num: page, page_size: size },
        filters,
        sorting: [{ direction: sortConfig.direction, field: sortConfig.field }]
    };

    return useBadgerFetch<PagedResponse<Basement>>({
        url: `${namespace}/basements/search`,
        method: 'post',
        withCredentials: true
    })(JSON.stringify(body));
}
