import React, { FC, ReactElement, useMemo } from 'react';
import { NoData } from 'shared/no-data';
import { TTreeNode } from 'api/typings';
import { EventDataNode } from 'rc-tree/lib/interface';
import Tree from 'rc-tree';

import './rc-tree.scss';
import styles from './badger-tree.module.scss';

interface Props {
    isLoading: boolean;
    height: number;
    nodes: TTreeNode[];
    onLoadData?: (treeNode: EventDataNode<TTreeNode>) => Promise<any>;
    itemHeight: number;
    titleRenderer: (node: TTreeNode) => ReactElement;
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
            disabled={isLoading}
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

    const renderData = useMemo(() => (nodes.length ? data : <NoData />), [nodes, data]);

    return (
        <div className={styles.container}>
            <div className={styles.data}>{isLoading && !nodes.length ? null : renderData}</div>
        </div>
    );
};
