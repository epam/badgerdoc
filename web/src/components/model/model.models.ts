import { Basement, Category, Model } from '../../api/typings';
import { Job } from '../../api/typings/jobs';

export type ModelValues = {
    baseModel?: Model;
    name?: string;
    basement?: Basement;
    categories?: Category[];
    id: string;
    score?: string;
    status?: string;
    type?: string;
    tenant?: string;
    training_id?: number;
    configuration_path_file?: string;
    configuration_path_bucket?: string;
    data_path_file?: string;
    data_path_bucket?: string;
    jobs?: Job[];
};

export const enum ActionTypeEnum {
    EDIT = 'edit',
    ADD = 'add'
}
