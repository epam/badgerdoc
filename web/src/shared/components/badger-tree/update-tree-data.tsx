import { TTreeNode } from 'api/typings';
import { isEmpty } from 'lodash';

export const updateTreeData = (
    list: TTreeNode[],
    key: string,
    children: TTreeNode[]
): TTreeNode[] =>
    list.map((node) => {
        if (node.key === key) {
            const combinedChildren = [...node.children, ...children];

            const uniqueChildren: TTreeNode[] = Array.from(
                new Set(combinedChildren.map((obj) => obj.key))
            )
                .map((key) => {
                    const foundObj = combinedChildren.find((obj) => obj.key === key);
                    return foundObj;
                })
                .filter((obj) => obj !== undefined) as TTreeNode[];

            return {
                ...node,
                children: uniqueChildren
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
