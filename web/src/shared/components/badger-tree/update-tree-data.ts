import { TreeNode } from 'api/typings';
import { isEmpty } from 'lodash';

export const updateTreeData = (list: TreeNode[], key: string, children: TreeNode[]): TreeNode[] =>
    list.map((node) => {
        if (node.key === key) {
            return {
                ...node,
                children
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
