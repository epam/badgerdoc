import { TTreeNode } from 'api/typings';
import { isEmpty } from 'lodash';

export const updateTreeData = (
    list: TTreeNode[],
    key: string,
    children: TTreeNode[]
): TTreeNode[] =>
    list.map((node) => {
        if (node.key === key) {
            return {
                ...node,
                children: [...node.children, ...children]
            };
        }
        if (node.children && !isEmpty(node.children)) {
            return {
                ...node,
                children: updateTreeData(node.children, key, children)
            };
        }
        return node;
    });
