import { PickerInput } from '@epam/loveship';
import { useArrayDataSource } from '@epam/uui';
import { LabeledInput } from '@epam/uui-components';
import { DocumentLinkWithName } from 'api/hooks/annotations';
import { Category, FileDocument } from 'api/typings';
import React, { FC, useMemo } from 'react';

import styles from './relations-panel.module.scss';

interface Props {
    categories?: Category[];
    documentLinks?: DocumentLinkWithName[];
    onLinkChanged: (documentId: number, categoryId: string) => void;
    selectedRelatedDoc?: FileDocument;
}
export const RelationsPanel: FC<Props> = ({
    categories,
    documentLinks,
    onLinkChanged,
    selectedRelatedDoc
}) => {
    const categoriesDataSource = useArrayDataSource(
        {
            items: categories?.filter((category) => category.type === 'document_link') ?? []
        },
        [categories]
    );

    const selectedCategoryId = useMemo(() => {
        if (documentLinks && selectedRelatedDoc) {
            return documentLinks?.find((documentLink) => documentLink.to === selectedRelatedDoc.id)
                ?.category;
        }
    }, [documentLinks, selectedRelatedDoc]);

    return (
        <div className={styles.relationsWrapper}>
            <LabeledInput label="Documents relation"></LabeledInput>
            <div className={styles.category}>
                <PickerInput
                    size="24"
                    dataSource={categoriesDataSource}
                    value={selectedCategoryId}
                    onValueChange={(cat: string) => {
                        onLinkChanged(selectedRelatedDoc?.id!, cat);
                    }}
                    getName={(item) => item?.name ?? ''}
                    entityName="Categories name"
                    selectionMode="single"
                    valueType={'id'}
                    sorting={{ field: 'name', direction: 'asc' }}
                    placeholder="Select relation between documents"
                />
            </div>
        </div>
    );
};
