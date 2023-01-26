import React, { FC, ReactElement, useMemo } from 'react';
import { NoData } from 'shared/no-data';
import { TreeNode } from 'api/typings';
import { EventDataNode } from 'rc-tree/lib/interface';
import Tree from 'rc-tree';
import { Spinner } from '@epam/loveship';

import './rc-tree.scss';
import styles from './badger-tree.module.scss';

interface Props {
    isLoading: boolean;
    height: number;
    nodes: TreeNode[];
    onLoadData?: (treeNode: EventDataNode<TreeNode>) => Promise<any>;
    itemHeight: number;
    titleRenderer: (node: TreeNode) => ReactElement;
    onSelect: (selectedKeys: any, info: any) => void;
    selectedKeys: string[];
    defaultExpandAll?: boolean;
}
export const BadgerTree: FC<Props> = ({
    isLoading,
    height,
    nodes,
    onLoadData,
    itemHeight,
    titleRenderer,
    onSelect,
    selectedKeys,
    defaultExpandAll
}) => {
    const data = (
        <Tree
            treeData={nodes}
            loadData={onLoadData}
            height={height}
            itemHeight={itemHeight}
            titleRender={titleRenderer}
            onSelect={onSelect}
            selectedKeys={selectedKeys}
            defaultExpandAll={defaultExpandAll}
        />
    );
    const spinner = <Spinner color="sky" />;
    const renderData = useMemo(() => (nodes.length ? data : <NoData />), [nodes]);

    return (
        <div className={styles.container}>
            <div className={styles.data}>{isLoading ? spinner : renderData}</div>
        </div>
    );
};
