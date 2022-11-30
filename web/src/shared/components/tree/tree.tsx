import { Spinner } from '@epam/loveship';
import { TreeNode } from 'api/typings';
import Tree from 'rc-tree';
import React, { FC, ReactElement } from 'react';
import './rc-tree.scss';
import { EventDataNode } from 'rc-tree/lib/interface';

interface Props {
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
    height,
    nodes,
    onLoadData,
    itemHeight,
    titleRenderer,
    onSelect,
    selectedKeys,
    defaultExpandAll
}) => {
    return (
        <div className="animation">
            <div style={{ display: 'flex' }}>
                <div style={{ flex: '1 1 50%' }}>
                    {nodes.length ? (
                        <Tree
                            treeData={nodes}
                            loadData={onLoadData}
                            height={height}
                            itemHeight={itemHeight}
                            titleRender={titleRenderer}
                            onSelect={onSelect}
                            selectedKeys={selectedKeys}
                            defaultExpandAll={defaultExpandAll}
                        ></Tree>
                    ) : (
                        <Spinner color="sky" />
                    )}
                </div>
            </div>
        </div>
    );
};
