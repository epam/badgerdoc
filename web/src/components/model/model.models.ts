import { Basement, Category, Model } from '../../api/typings';
import { Job } from '../../api/typings/jobs';

export type ModelValues = {
    baseModel?: Model;
    name: string | undefined;
    basement: Basement | undefined;
    categories: Category[] | undefined;
    id: string;
    score: string | undefined;
    status?: string;
    type: string | undefined;
    tenant?: string | undefined;
    training_id?: number | undefined;
    configuration_path_file?: string | undefined;
    configuration_path_bucket?: string | undefined;
    data_path_file?: string | undefined;
    data_path_bucket?: string | undefined;
    jobs: Job[] | undefined;
};
