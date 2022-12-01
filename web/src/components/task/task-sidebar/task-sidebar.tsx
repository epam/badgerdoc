import React, { FC, ReactElement, useEffect, useMemo, useState } from 'react';
import {
    Button,
    FlexRow,
    LabeledInput,
    MultiSwitch,
    NumericInput,
    RadioGroup,
    TabButton
} from '@epam/loveship';
import { useUuiContext } from '@epam/uui';
import { useSetTaskFinished, useGetValidatedPages } from 'api/hooks/tasks';
import { useTaskAnnotatorContext } from 'connectors/task-annotator-connector/task-annotator-context';
import {
    FinishTaskValidationModal,
    TaskValidationValues
} from '../task-modal/task-validation-modal';
import styles from './task-sidebar.module.scss';
import { CategoriesSelectionModeToggle } from 'components/categories/categories-selection-mode-toggle/categories-selection-mode-toggle';
import { useTableAnnotatorContext } from '../../../shared/components/annotator/context/table-annotator-context';
import { TaskSidebarData } from '../task-sidebar-data/task-sidebar-data';
import {
    AnnotationBoundMode,
    AnnotationBoundType,
    AnnotationImageToolType,
    AnnotationLinksBoundType,
    Maybe
} from 'shared';

import { Status } from 'shared/components/status';
import { mapStatusForValidationPage } from 'shared/helpers/map-statuses';
import { ValidationPageStatus } from 'api/typings/tasks';
import { ReactComponent as MergeIcon } from '@epam/assets/icons/common/editor-table_merge_cells-24.svg';
import { ReactComponent as SplitIcon } from '@epam/assets/icons/common/editor-table_split_cells-24.svg';
import { Tooltip } from '@epam/loveship';
import { Category } from '../../../api/typings';
import { ImageToolsParams } from './image-tools-params';
import { CategoriesTab } from 'components/categories/categories-tab/categories-tab';

type TaskSidebarProps = {
    onRedirectAfterFinish: () => void;
    jobSettings?: ReactElement;
    viewMode: boolean;
};

const TaskSidebar: FC<TaskSidebarProps> = ({ onRedirectAfterFinish, jobSettings, viewMode }) => {
    const {
        annDataAttrs,
        task,
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
        sortedUsers,
        isOwner,
        selectionType,
        isDataTabDisabled,
        isCategoryDataEmpty,
        onValidClick,
        onInvalidClick,
        onCategorySelected,
        onSaveTask,
        onAnnotationTaskFinish,
        onEditClick,
        onClearTouchedPages,
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
        setSelectedToolParams
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

    const isValidationDisabled = !currentPage && !isAnnotatable;

    const svc = useUuiContext();
    const onSaveForm = async (formOptions: TaskValidationValues) => {
        if (task && (formOptions.option_invalid || formOptions.option_edited)) {
            await useSetTaskFinished(task?.id, {
                option_edited: formOptions.option_edited,
                option_invalid: formOptions.option_invalid
            });
        }
    };
    const onSaveValidForm = () => {
        if (task) {
            useSetTaskFinished(task?.id);
        }
    };
    const [allValid, setAllvalid] = useState(true);
    const [allValidated, setAllValidated] = useState(true);
    const [invalidPageCount, setInvalidPageCount] = useState(0);
    const [editedPageCount, setEditedPageCount] = useState(0);
    const [boundModeSwitch, setBoundModeSwitch] = useState<AnnotationBoundMode>('box');
    const [tableModeValues, setTableModeValues] = useState<string>('');

    const { data: pages, refetch } = useGetValidatedPages(
        { taskId: task?.id, taskType: task?.is_validation },
        {}
    );

    const getFirstCategory = (boundMode: AnnotationBoundMode): Maybe<Category[]> => {
        return categories?.filter((el) => el.type === boundMode);
    };

    useEffect(() => {
        let newSelectionType:
            | AnnotationBoundType
            | AnnotationImageToolType
            | AnnotationLinksBoundType;
        switch (boundModeSwitch) {
            case 'box':
                newSelectionType = 'box';
                break;
            case 'link':
                newSelectionType = 'Chain';
                break;
            case 'segmentation':
                newSelectionType = 'polygon';
                onChangeSelectedTool('pen');

                break;
            default:
                newSelectionType = 'free-box';
        }
        const cats = getFirstCategory(boundModeSwitch);
        if (cats) {
            onCategorySelected(cats[0] as Category);
        }
        onChangeSelectionType(newSelectionType);
    }, [boundModeSwitch]);

    useEffect(() => {
        if (task?.is_validation && pages) {
            if (pages?.failed_validation_pages || pages?.annotated_pages || pages?.not_processed) {
                setAllvalid(false);
                setInvalidPageCount(pages.failed_validation_pages.length);
                setEditedPageCount(pages?.annotated_pages.length);
                if (
                    pages?.failed_validation_pages.length === 0 &&
                    pages?.not_processed.length === 0 &&
                    pages.validated
                ) {
                    setAllvalid(true);
                }
            }
            if (pages?.not_processed.length !== 0) {
                setAllValidated(false);
                return;
            }
            setAllValidated(true);
        }
    }, [pages, validPages, invalidPages]);

    useEffect(() => {
        if (tableMode) setTabValue('Data');
    }, [tableMode]);

    const disableSave = useMemo(() => {
        return (
            (isValidation && touchedPages.length === 0) ||
            !isAnnotatable ||
            (!isValidation && modifiedPages.length === 0)
        );
    }, [validPages, invalidPages, touchedPages, modifiedPages, editedPages]);

    useEffect(() => {
        if (tableModeValues === 'cells') setIsCellMode(true);
        else setIsCellMode(false);
    }, [tableModeValues]);

    const SaveButton = (
        <div className="flex flex-center">
            <div
                className={
                    disableSave ? styles['hot-key-container-disabled'] : styles['hot-key-container']
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

    return (
        <div className={`${styles.container} flex-col`}>
            <div className={`${styles.main} flex-col`}>
                <FlexRow borderBottom="night50" background="none" cx="justify-center">
                    <TabButton
                        caption={'Categories'}
                        isLinkActive={tabValue === 'Categories'}
                        onClick={() => setTabValue('Categories')}
                        size="36"
                    />

                    <TabButton
                        caption="Data"
                        isDisabled={isDataTabDisabled}
                        isLinkActive={tabValue === 'Data'}
                        onClick={() => setTabValue('Data')}
                        size="36"
                    />

                    <TabButton
                        caption="Information"
                        isLinkActive={tabValue === 'Information'}
                        onClick={() => setTabValue('Information')}
                        size="36"
                    />
                    <TabButton
                        caption={'Settings'}
                        isLinkActive={tabValue === 'Settings'}
                        onClick={() => setTabValue('Settings')}
                        size="36"
                    />
                </FlexRow>
                <div className={`${styles.tabs} flex-col flex-cell`}>
                    {isValid || isInvalid ? (
                        <div className={validationStyle}>
                            <Status
                                statusTitle={mapStatusForValidationPage(validationStatus).title}
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
                                />
                            )}
                        </>
                    )}
                    {tabValue === 'Data' && tableMode && (
                        <>
                            <div className={styles.multiswitch}>
                                <MultiSwitch
                                    items={[
                                        { id: 'lines', caption: 'Lines' },
                                        { id: 'cells', caption: 'Cells' }
                                    ]}
                                    value={tableModeValues}
                                    onValueChange={setTableModeValues}
                                />
                            </div>

                            {tableModeValues === 'lines' && (
                                <div className={styles.tableParams}>
                                    <LabeledInput label="Columns">
                                        <NumericInput
                                            value={tableModeColumns}
                                            onValueChange={setTableModeColumns}
                                            min={1}
                                            max={10}
                                        />
                                    </LabeledInput>
                                    <span>X</span>
                                    <LabeledInput label="Rows">
                                        <NumericInput
                                            value={tableModeRows}
                                            onValueChange={setTableModeRows}
                                            min={1}
                                            max={10}
                                        />
                                    </LabeledInput>
                                </div>
                            )}
                            {tableModeValues === 'cells' && (
                                <div>
                                    <div className={styles.mergeButton}>
                                        <RadioGroup
                                            items={categories
                                                ?.filter((el) => el.parent === 'table')
                                                .map((el) => ({
                                                    id: el.name,
                                                    name: el.name,
                                                    renderLabel: (el: any) => (
                                                        <span style={{ color: el.metadata?.color }}>
                                                            {el.name}
                                                        </span>
                                                    ),
                                                    renderName: (s: any) => (
                                                        <span style={{ color: el.metadata?.color }}>
                                                            {el.name}
                                                        </span>
                                                    )
                                                }))}
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
                        />
                    )}
                    {tabValue === 'Information' && (
                        <div className={styles.information}>
                            {task ? (
                                <>
                                    <div className={styles['metadata-item']}>
                                        <span className={styles['metadata-item__name']}>
                                            Document:
                                        </span>
                                        <span className={styles['metadata-item__value']}>
                                            {`${fileMetaInfo.name}`}
                                        </span>
                                    </div>
                                    <div className={styles['metadata-item']}>
                                        <span className={styles['metadata-item__name']}>
                                            TaskId:
                                        </span>
                                        <span className={styles['metadata-item__value']}>
                                            {`${task?.id}`}
                                        </span>
                                    </div>
                                    <div className={styles['metadata-item']}>
                                        <span className={styles['metadata-item__name']}>
                                            Pages:
                                        </span>
                                        <span className={styles['metadata-item__value']}>
                                            {`${task?.pages.join(', ')}`}
                                        </span>
                                    </div>
                                    <div className={styles['metadata-item']}>
                                        <span className={styles['metadata-item__name']}>
                                            Job Name:
                                        </span>
                                        <span className={styles['metadata-item__value']}>
                                            {`${task?.job.name}`}
                                        </span>
                                    </div>
                                    <div className={styles['metadata-item']}>
                                        <span className={styles['metadata-item__name']}>
                                            Deadline:
                                        </span>
                                        <span className={styles['metadata-item__value']}>
                                            {`${task?.deadline}`}
                                        </span>
                                    </div>
                                    <div className={styles['metadata-item']}>
                                        <span className={styles['metadata-item__name']}>
                                            Status:
                                        </span>
                                        <span className={styles['metadata-item__value']}>
                                            {`${task?.status}`}
                                        </span>
                                    </div>
                                </>
                            ) : (
                                <>
                                    {jobSettings}
                                    <div className={styles['metadata-item']}>
                                        <span className={styles['metadata-item__name']}>
                                            Document ID:
                                        </span>
                                        <span className={styles['metadata-item__value']}>
                                            {`${fileMetaInfo.id}`}
                                        </span>
                                    </div>
                                    <div className={styles['metadata-item']}>
                                        <span className={styles['metadata-item__name']}>
                                            Pages:
                                        </span>
                                        <span className={styles['metadata-item__value']}>
                                            {fileMetaInfo.pages}
                                        </span>
                                    </div>
                                    <div className={styles['metadata-item']}>
                                        <span className={styles['metadata-item__name']}>Time:</span>
                                        <span className={styles['metadata-item__value']}>
                                            {fileMetaInfo.lastModified?.toString()}
                                        </span>
                                    </div>
                                </>
                            )}
                        </div>
                    )}

                    {isValidation ? (
                        <div className="flex justify-around">
                            {!editPage && (
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
                            )}
                            {!isInvalid && !editPage && (
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
                            )}
                            {editPage && (
                                <Button
                                    cx={styles.validation}
                                    caption="CANCEL"
                                    fill="none"
                                    color="sky"
                                    onClick={onCancelClick}
                                    isDisabled={isValidationDisabled}
                                />
                            )}
                            {!editPage && isInvalid && (
                                <Button
                                    cx={styles.validation}
                                    caption="EDIT"
                                    fill="none"
                                    color="sky"
                                    onClick={() => {
                                        onEditClick();
                                    }}
                                    isDisabled={isValidationDisabled}
                                />
                            )}
                            {editPage && (
                                <Button
                                    cx={styles.validation}
                                    caption="SAVE EDITS"
                                    fill="none"
                                    color="sky"
                                    onClick={() => {
                                        onAddTouchedPage();
                                        onSaveEditClick();
                                        refetch();
                                    }}
                                    isDisabled={isValidationDisabled}
                                />
                            )}
                        </div>
                    ) : (
                        ''
                    )}
                </div>
            </div>
            {task && ( // todo: add "EDIT ANNOTATION" button here if no task
                <Tooltip
                    content={disableSave ? 'Please modify annotation to enable save button' : ''}
                >
                    <Button
                        caption={SaveButton}
                        fill="white"
                        onClick={async () => {
                            await onSaveTask();
                            onClearTouchedPages();
                            refetch();
                        }}
                        cx={styles.button}
                        isDisabled={disableSave}
                    />
                </Tooltip>
            )}
            {isValidation && (
                <Tooltip
                    content={
                        allValidated
                            ? ''
                            : 'Please validate all page to finish task. Remaining pages: ' +
                              pages?.not_processed?.join(', ')
                    }
                >
                    <Button
                        cx={styles['button-finish']}
                        caption={'FINISH VALIDATION'}
                        isDisabled={!allValidated}
                        captionCX
                        onClick={async () => {
                            await svc.uuiModals.show<TaskValidationValues>((props) => (
                                <FinishTaskValidationModal
                                    onSaveForm={onSaveForm}
                                    allValid={allValid}
                                    allUsers={sortedUsers.current}
                                    currentUser={task?.user_id || ''}
                                    isOwner={isOwner}
                                    invalidPages={invalidPageCount}
                                    editedPageCount={editedPageCount}
                                    validSave={onSaveValidForm}
                                    {...props}
                                />
                            ));
                            onRedirectAfterFinish();
                        }}
                    />
                </Tooltip>
            )}
            {!viewMode && !isValidation && (
                <Button
                    cx={styles['button-finish']}
                    caption={'FINISH LABELING'}
                    onClick={onAnnotationTaskFinish}
                />
            )}
        </div>
    );
};

export default TaskSidebar;
