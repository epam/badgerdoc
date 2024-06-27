// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import React, { FC, ReactElement, useEffect, useMemo, useState } from 'react';
import {
    Button,
    FlexRow,
    LabeledInput,
    MultiSwitch,
    NumericInput,
    Panel,
    RadioGroup,
    TabButton,
    Tooltip,
    TextInput
} from '@epam/loveship';
import { useGetPageSummary } from 'api/hooks/tasks';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';

import { CategoriesSelectionModeToggle } from 'components/categories/categories-selection-mode-toggle/categories-selection-mode-toggle';
import { useTableAnnotatorContext } from '../../../shared/components/annotator/context/table-annotator-context';
import { TaskSidebarData } from '../task-sidebar-data/task-sidebar-data';
import {
    Annotation,
    AnnotationBoundMode,
    AnnotationBoundType,
    AnnotationImageToolType,
    AnnotationLinksBoundType
} from 'shared';
import { Status } from 'shared/components/status';
import { mapStatusForValidationPage } from 'shared/helpers/map-statuses';
import { ValidationPageStatus } from 'api/typings/tasks';
import { Label } from '../../../api/typings';
import { ImageToolsParams } from './image-tools-params';
import { CategoriesTab } from 'components/categories/categories-tab/categories-tab';
import { useLinkTaxonomyByCategoryAndJobId } from 'api/hooks/taxons';
import { TaskSidebarLabelsLinks } from './task-sidebar-labels-links/task-sidebar-labels-links';
import { NoData } from 'shared/no-data';
import { ReactComponent as MergeIcon } from '@epam/assets/icons/common/editor-table_merge_cells-24.svg';
import { ReactComponent as SplitIcon } from '@epam/assets/icons/common/editor-table_split_cells-24.svg';

import { getCategoryDataAttrs } from 'connectors/task-annotator-connector/task-annotator-utils';
import { FinishButton } from './finish-button/finish-button';
import { TABS, VISIBILITY_SETTING_ID } from './constants';
import { ReactComponent as openIcon } from '@epam/assets/icons/common/navigation-chevron-left_left-18.svg';
import { ReactComponent as closeIcon } from '@epam/assets/icons/common/navigation-chevron-right_right-18.svg';
import { ReactComponent as Copy } from '@epam/assets/icons/common/copy_content-12.svg';
import { handleCopy } from 'shared/helpers/copy-text';
import { getSaveButtonTooltipContent } from './utils';

import styles from './task-sidebar.module.scss';

type TaskSidebarProps = {
    jobSettings?: ReactElement;
    viewMode: boolean;
    isNextTaskPresented?: boolean;
};

const TaskSidebar: FC<TaskSidebarProps> = ({ jobSettings, viewMode, isNextTaskPresented }) => {
    const [isHidden, setIsHidden] = useState<boolean>(() => {
        const savedValue = localStorage.getItem(VISIBILITY_SETTING_ID);
        return savedValue ? JSON.parse(savedValue) : false;
    });
    const [tableModeValues, setTableModeValues] = useState<string>('');
    const [boundModeSwitch, setBoundModeSwitch] = useState<AnnotationBoundMode>('box');

    const {
        annDataAttrs,
        task,
        job,
        categories,
        fileMetaInfo,
        currentPage,
        validPages,
        invalidPages,
        selectedAnnotation,
        editedPages,
        touchedPages,
        modifiedPages,
        tabValue,
        selectionType,
        annotationType,
        isCategoryDataEmpty,
        onValidClick,
        onInvalidClick,
        onSaveTask,
        onAnnotationTaskFinish,
        onEditClick,
        onClearTouchedPages,
        onClearModifiedPages,
        clearAnnotationsChanges,
        onAddTouchedPage,
        onCancelClick,
        onSaveEditClick,
        setTabValue,
        onChangeSelectionType,
        onDataAttributesChange,
        onAnnotationEdited,
        tableMode,
        tableCellCategory,
        setTableCellCategory,
        selectedTool,
        onChangeSelectedTool,
        selectedToolParams,
        setSelectedToolParams,
        onLabelsSelected,
        setSelectedLabels,
        selectedLabels,
        latestLabelsId,
        isDocLabelsModified,
        getJobId,
        documentLinks,
        onRelatedDocClick,
        selectedRelatedDoc,
        documentLinksChanged,
        onFinishSplitValidation,
        allValidated,
        annotationSaved,
        onFinishValidation,
        notProcessedPages,
        currentCell,
        allAnnotations
    } = useTaskAnnotatorContext();
    const {
        tableModeColumns,
        tableModeRows,
        setTableModeRows,
        setTableModeColumns,
        setIsCellMode,
        cellsSelected,
        onMergeCellsClicked,
        selectedCellsCanBeMerged,
        onSplitCellsClicked,
        selectedCellsCanBeSplitted
    } = useTableAnnotatorContext();
    const isValidation = task?.is_validation;
    const isAnnotatable = task?.status === 'In Progress' || task?.status === 'Ready';
    const isValid = validPages.includes(currentPage);
    const isInvalid = invalidPages.includes(currentPage);
    const editPage = editedPages.includes(currentPage);
    const splitValidation = isValidation && job?.validation_type === 'extensive_coverage';

    const isValidationDisabled = (!currentPage && !splitValidation) || !isAnnotatable;

    const { refetch } = useGetPageSummary({ taskId: task?.id, taskType: task?.is_validation }, {});

    const [cell, setCell] = useState<string | undefined>('');
    const [annotation, setAnnotation] = useState<Annotation>();

    useEffect(() => {
        setCell(currentCell?.text);
    }, [currentCell]);

    useEffect(() => {
        if (allAnnotations) {
            const annotation = allAnnotations[currentPage];
            if (annotation) {
                setAnnotation(annotation[0]);
            }
        }
    }, [allAnnotations]);

    useEffect(() => {
        let newSelectionType:
            | AnnotationBoundType
            | AnnotationImageToolType
            | AnnotationLinksBoundType;
        switch (boundModeSwitch) {
            case 'box':
                newSelectionType = annotationType;
                break;
            case 'link':
                newSelectionType = AnnotationLinksBoundType.chain;
                break;
            case 'segmentation':
                newSelectionType = 'polygon';
                onChangeSelectedTool('pen');

                break;
            default:
                newSelectionType = 'free-box';
        }
        onChangeSelectionType(newSelectionType);
    }, [boundModeSwitch]);

    useEffect(() => {
        if (tableMode) setTabValue('Data');
    }, [tableMode]);

    const isSaveButtonDisabled = useMemo(() => {
        if (isDocLabelsModified || documentLinksChanged) return false;
        return (
            (isValidation && !splitValidation && touchedPages.length === 0) ||
            ((!isValidation || splitValidation) && modifiedPages.length === 0) ||
            !isAnnotatable ||
            annotationSaved
        );
    }, [
        validPages,
        invalidPages,
        touchedPages,
        modifiedPages,
        editedPages,
        isDocLabelsModified,
        documentLinksChanged,
        annotationSaved
    ]);

    useEffect(() => {
        if (tableModeValues === 'cells') setIsCellMode(true);
        else setIsCellMode(false);
    }, [tableModeValues]);

    const SaveButton = (
        <div className="flex flex-center">
            <div
                className={
                    isSaveButtonDisabled
                        ? styles['hot-key-container-disabled']
                        : styles['hot-key-container']
                }
            >
                Ctrl + S
            </div>
            <span className={styles['custom-button']}>SAVE DRAFT</span>
        </div>
    );

    const validationStyle = `${styles['validation-color']} flex flex-center ${
        isValid ? styles.validColor : styles.invalidColor
    }`;
    const validationStatus: ValidationPageStatus = isValid ? 'Valid Page' : 'Invalid Page';

    const jobId = useMemo(() => getJobId(), [getJobId]);

    useEffect(() => {
        if (categories) {
            const latestLabels: Label[] = categories
                .filter((category) => latestLabelsId?.includes(category.id))
                .map((category) => {
                    return { name: category.name, id: category.id };
                });
            setSelectedLabels(latestLabels);
        }
    }, [categories, latestLabelsId]);

    const dataAttrsWithTaxonomy = useMemo(() => {
        if (!selectedAnnotation || !categories) return;
        return getCategoryDataAttrs(selectedAnnotation?.category, categories)?.filter(
            (dataAttr) => dataAttr.type === 'taxonomy'
        );
    }, [selectedAnnotation, categories]);

    const { data: taxonomy } = useLinkTaxonomyByCategoryAndJobId(
        {
            jobId,
            categoryId: selectedAnnotation?.category!
        },
        { enabled: !!dataAttrsWithTaxonomy?.length }
    );

    const cellsItems: {
        id: string;
        name: string;
        renderLabel: (el: any) => React.ReactNode;
        renderName: () => React.ReactNode;
    }[] = useMemo(
        () =>
            categories
                ?.filter((el) => el.parent === 'table')
                .map((el) => ({
                    id: el.name,
                    name: el.name,
                    renderLabel: (el: any) => (
                        <span
                            style={{
                                color: el.metadata?.color
                            }}
                        >
                            {el.name}
                        </span>
                    ),
                    // eslint-disable-next-line react/display-name
                    renderName: () => (
                        <span
                            style={{
                                color: el.metadata?.color
                            }}
                        >
                            {el.name}
                        </span>
                    )
                })) || [],
        [categories]
    );

    const taskInfoElements = [
        {
            name: 'Document:',
            value: `${fileMetaInfo.name}`,
            additional: (
                <Copy
                    className={styles.copyIcon}
                    onClick={(e) => handleCopy(e, fileMetaInfo.name)}
                />
            )
        },
        { name: 'TaskId:', value: `${task?.id}` },
        { name: 'Pages:', value: `${task?.pages.join(', ')}` },
        { name: 'Job Name:', value: `${task?.job.name}` },
        { name: 'Deadline:', value: `${task?.deadline ?? ''}` },
        { name: 'Status:', value: `${task?.status}` }
    ];
    const taskInfo = (
        <>
            {taskInfoElements.map((el) => (
                <div className={styles['metadata-item']} key={el.name}>
                    <span className={styles['metadata-item__name']}>{el.name}</span>
                    <div className={styles.valueWrapper}>
                        <span className={styles['metadata-item__value']}>{el.value}</span>
                        {el.additional}
                    </div>
                </div>
            ))}
        </>
    );

    const docInfoElements = [
        { name: 'Document ID:', value: `${fileMetaInfo.id}` },
        { name: 'Pages:', value: `${fileMetaInfo.pages}` },
        { name: 'Time:', value: `${fileMetaInfo.lastModified?.toString()}` }
    ];
    const docInfo = (
        <>
            {jobSettings}
            {docInfoElements.map((el) => (
                <div className={styles['metadata-item']} key={el.name}>
                    <span className={styles['metadata-item__name']}>{el.name}</span>
                    <span className={styles['metadata-item__value']}>{el.value}</span>
                </div>
            ))}
        </>
    );

    const handleSave = async () => {
        await onSaveTask();
        onClearTouchedPages();
        onClearModifiedPages();
        clearAnnotationsChanges();
        refetch();
    };

    const handleSaveEdits = async () => {
        onAddTouchedPage();
        await onSaveEditClick();
        refetch();
    };

    const handleToggleVisibility = () => {
        localStorage.setItem(VISIBILITY_SETTING_ID, String(!isHidden));
        setIsHidden(!isHidden);
    };

    const saveButtonTooltipContent = getSaveButtonTooltipContent(
        isSaveButtonDisabled,
        task?.status,
        isValidation
    );

    const handleCellChange = (value: string) => {
        setCell(value);
        if (annotation) {
            const editedTableCells = annotation.tableCells?.map((tableCell: Annotation) => {
                let text = tableCell.text;
                if (tableCell?.id === currentCell?.id) {
                    text = value;
                }

                return {
                    ...tableCell,
                    text
                };
            });
            onAnnotationEdited(currentPage, annotation.id, {
                tableCells: editedTableCells
            });
        }
    };

    return (
        <Panel cx={styles.wrapper}>
            <Button
                fill="none"
                cx={styles.hideIcon}
                onClick={handleToggleVisibility}
                icon={isHidden ? openIcon : closeIcon}
            />
            {!isHidden && (
                <div className={`${styles.container} flex-col`}>
                    <div className={`${styles.main} flex-col`}>
                        <FlexRow borderBottom="night50" background="none" cx="justify-center">
                            {TABS.map((tabName) => (
                                <TabButton
                                    size="36"
                                    key={tabName}
                                    caption={tabName}
                                    isLinkActive={tabValue === tabName}
                                    onClick={() => setTabValue(tabName)}
                                />
                            ))}
                        </FlexRow>
                        <div className={`${styles.tabs} flex-col flex-cell`}>
                            {!splitValidation && (isValid || isInvalid) ? (
                                <div className={validationStyle}>
                                    <Status
                                        statusTitle={
                                            mapStatusForValidationPage(validationStatus).title
                                        }
                                        color={mapStatusForValidationPage(validationStatus).color}
                                    />
                                </div>
                            ) : null}
                            {tabValue === 'Categories' && (
                                <>
                                    <CategoriesTab
                                        boundModeSwitch={boundModeSwitch}
                                        setBoundModeSwitch={setBoundModeSwitch}
                                    />
                                    {boundModeSwitch === 'segmentation' && (
                                        <ImageToolsParams
                                            onChangeToolParams={(e) => {
                                                setSelectedToolParams({
                                                    type: selectedToolParams.type,
                                                    values: e
                                                });
                                            }}
                                            selectedTool={selectedTool}
                                            toolParams={selectedToolParams}
                                        />
                                    )}
                                    {!viewMode && (
                                        <CategoriesSelectionModeToggle
                                            selectionType={selectionType}
                                            onChangeSelectionType={onChangeSelectionType}
                                            selectionMode={boundModeSwitch}
                                            fileMetaInfo={fileMetaInfo}
                                            selectedTool={selectedTool}
                                            onChangeSelectedTool={onChangeSelectedTool}
                                            isDisabled={!isAnnotatable}
                                        />
                                    )}
                                </>
                            )}
                            {tabValue === 'Data' && tableMode && (
                                <>
                                    <MultiSwitch
                                        items={[
                                            { id: 'lines', caption: 'Lines' },
                                            { id: 'cells', caption: 'Cells' }
                                        ]}
                                        value={tableModeValues}
                                        onValueChange={setTableModeValues}
                                    />
                                    {tableModeValues === 'lines' && (
                                        <div className={styles.tableParams}>
                                            <LabeledInput label="Columns">
                                                <NumericInput
                                                    value={tableModeColumns}
                                                    onValueChange={setTableModeColumns}
                                                    min={1}
                                                    max={20}
                                                />
                                            </LabeledInput>
                                            <span>X</span>
                                            <LabeledInput label="Rows">
                                                <NumericInput
                                                    value={tableModeRows}
                                                    onValueChange={setTableModeRows}
                                                    min={1}
                                                    max={20}
                                                />
                                            </LabeledInput>
                                        </div>
                                    )}
                                    {tableModeValues === 'cells' && (
                                        <div>
                                            <div className={styles.mergeButton}>
                                                <RadioGroup
                                                    items={cellsItems}
                                                    value={tableCellCategory}
                                                    onValueChange={setTableCellCategory}
                                                    direction="vertical"
                                                    isDisabled={
                                                        !(cellsSelected && selectedCellsCanBeMerged)
                                                    }
                                                />
                                            </div>
                                            <div className={styles.mergeButton}>
                                                <Button
                                                    color={'sky'}
                                                    caption={'Merge'}
                                                    icon={MergeIcon}
                                                    isDisabled={
                                                        !(cellsSelected && selectedCellsCanBeMerged)
                                                    }
                                                    fill={'none'}
                                                    onClick={() => onMergeCellsClicked(true)}
                                                />
                                            </div>
                                            {cellsSelected && selectedCellsCanBeSplitted && (
                                                <div className={styles.mergeButton}>
                                                    <Button
                                                        color={'sky'}
                                                        caption={'Split'}
                                                        icon={SplitIcon}
                                                        fill={'none'}
                                                        onClick={() => onSplitCellsClicked(true)}
                                                    />
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    <div className={styles.cellInput}>
                                        <LabeledInput label="Value">
                                            <TextInput
                                                value={cell}
                                                cx="c-m-t-5"
                                                onValueChange={handleCellChange}
                                                rawProps={{
                                                    style: {
                                                        width: '200px'
                                                    }
                                                }}
                                            />
                                        </LabeledInput>
                                    </div>
                                </>
                            )}
                            {tabValue === 'Data' && !tableMode && (
                                <TaskSidebarData
                                    annDataAttrs={annDataAttrs}
                                    selectedAnnotation={selectedAnnotation}
                                    isCategoryDataEmpty={isCategoryDataEmpty}
                                    onDataAttributesChange={onDataAttributesChange}
                                    viewMode={viewMode}
                                    onAnnotationEdited={onAnnotationEdited}
                                    currentPage={currentPage}
                                    taxonomyId={(taxonomy || [])[0]?.id}
                                />
                            )}
                            {tabValue === 'Information' && (
                                <div className={styles.information}>
                                    {task ? taskInfo : docInfo}
                                </div>
                            )}
                            {tabValue === 'Document' && categories !== undefined && (
                                <TaskSidebarLabelsLinks
                                    viewMode={viewMode}
                                    jobId={jobId}
                                    onLabelsSelected={onLabelsSelected}
                                    selectedLabels={selectedLabels ?? []}
                                    documentLinks={documentLinks}
                                    onRelatedDocClick={onRelatedDocClick}
                                    selectedRelatedDoc={selectedRelatedDoc}
                                />
                            )}
                            {tabValue === 'Document' && categories === undefined && (
                                <NoData title="There are no categories" />
                            )}
                            {isValidation && !splitValidation && (
                                <div className="flex justify-around">
                                    {!editPage && (
                                        <>
                                            <Button
                                                key={`valid${currentPage}`}
                                                cx={styles.validation}
                                                caption="Valid"
                                                fill={isValid ? undefined : 'none'}
                                                color="grass"
                                                onClick={
                                                    isValid
                                                        ? undefined
                                                        : () => {
                                                              onValidClick();
                                                              onAddTouchedPage();
                                                          }
                                                }
                                                isDisabled={isValidationDisabled}
                                            />

                                            {!isInvalid ? (
                                                <Button
                                                    key={`invalid${currentPage}`}
                                                    cx={styles.validation}
                                                    caption="Invalid"
                                                    fill={isInvalid ? undefined : 'none'}
                                                    color="fire"
                                                    onClick={
                                                        isInvalid
                                                            ? undefined
                                                            : () => {
                                                                  onInvalidClick();
                                                                  onAddTouchedPage();
                                                              }
                                                    }
                                                    isDisabled={isValidationDisabled}
                                                />
                                            ) : (
                                                <Button
                                                    cx={styles.validation}
                                                    caption="EDIT"
                                                    fill="none"
                                                    color="sky"
                                                    onClick={onEditClick}
                                                    isDisabled={isValidationDisabled}
                                                />
                                            )}
                                        </>
                                    )}
                                    {editPage && !annotationSaved && (
                                        <>
                                            <Button
                                                cx={styles.validation}
                                                caption="CANCEL"
                                                fill="none"
                                                color="sky"
                                                onClick={onCancelClick}
                                                isDisabled={isValidationDisabled}
                                            />
                                            <Button
                                                cx={styles.validation}
                                                caption="SAVE EDITS"
                                                fill="none"
                                                color="sky"
                                                onClick={handleSaveEdits}
                                                isDisabled={isValidationDisabled}
                                            />
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                    {task && ( // todo: add "EDIT ANNOTATION" button here if no task
                        <Tooltip content={saveButtonTooltipContent}>
                            <Button
                                caption={SaveButton}
                                fill="white"
                                onClick={handleSave}
                                cx={styles.button}
                                isDisabled={isSaveButtonDisabled}
                            />
                        </Tooltip>
                    )}
                    <FinishButton
                        viewMode={viewMode}
                        isAnnotatable={isAnnotatable}
                        allValidated={allValidated}
                        isNextTaskPresented={isNextTaskPresented}
                        isValidation={Boolean(isValidation)}
                        isSplitValidation={Boolean(splitValidation)}
                        notProcessedPages={notProcessedPages}
                        onFinishValidation={onFinishValidation}
                        onAnnotationTaskFinish={onAnnotationTaskFinish}
                        onFinishSplitValidation={onFinishSplitValidation}
                        onSaveTask={onSaveTask}
                        jobType={job?.validation_type}
                        taskStatus={task?.status}
                    />
                </div>
            )}
        </Panel>
    );
};

export default TaskSidebar;
