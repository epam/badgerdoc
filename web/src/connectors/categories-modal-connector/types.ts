import { IModal } from '@epam/uui';
import { Category, CategoryDataAttribute, CategoryType } from 'api/typings';

export interface TaskValidationValues {
    categoryValue?: Category;
}
export interface IProps extends IModal<TaskValidationValues> {
    categoryValue?: Category;
}
export type TCategoryOption = { id: CategoryType; name: CategoryType };

export type TFormValues = {
    name: string;
    color: string;
    type: CategoryType;
    categoryId: string;
    dataAttributes: CategoryDataAttribute[];
    parentId: string | null;
    withParentLabel: boolean;
};
