import { useState, useMemo } from 'react';
import { OWNER_TAB } from '../../components/task/task-sidebar-flow/constants';
import { getCategoriesByUserId } from '../../components/task/task-sidebar-flow/utils';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';

export const useLabels = () => {
    const [currentTab, setCurrentTab] = useState(OWNER_TAB.id);
    const { categories, selectedLabels, latestRevisionByAnnotators } = useTaskAnnotatorContext();
    const categoriesByUserId = useMemo(
        () => getCategoriesByUserId(latestRevisionByAnnotators, categories),
        [latestRevisionByAnnotators, categories]
    );
    const labelsByTab = {
        ...categoriesByUserId,
        [OWNER_TAB.id]: selectedLabels
    };
    const labels = labelsByTab[currentTab];

    return { currentTab, setCurrentTab, labels };
};
