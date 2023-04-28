import React, { FC } from 'react';
import { Dropdown, IconButton, Panel } from '@epam/loveship';
import { Annotation } from 'shared';

import { ReactComponent as linksIcon } from '@epam/assets/icons/common/navigation-more_vert-18.svg';
import { ReactComponent as outgoingLinkIcon } from '@epam/assets/icons/common/navigation-chevron-down-18.svg';
import { ReactComponent as incomingLinkIcon } from '@epam/assets/icons/common/navigation-chevron-up-18.svg';
import { Link } from 'api/typings';

import { LinkRow } from './link-row';

export const Links: FC<{
    links?: Annotation['links'];
    incomingLinks?: Annotation['links'];
    annotationId: Annotation['id'];
    isEditable: boolean;
    annotationNameById: Record<string, string>;
    annotationPageNum?: number;
    onLinkDeleted: (pageNum: number, annotationId: Annotation['id'], link: Link) => void;
    onSelect: (id: Annotation['id']) => void;
}> = ({
    annotationId,
    annotationNameById,
    incomingLinks,
    links,
    onLinkDeleted,
    onSelect,
    isEditable,
    annotationPageNum = 1
}) => {
    return (
        <Dropdown
            renderBody={({ onClose }) => (
                <Panel background="white" shadow>
                    {links?.map((link) => (
                        <LinkRow
                            isEditable={isEditable}
                            key={link.to}
                            to={link.to}
                            icon={outgoingLinkIcon}
                            annotationName={annotationNameById[link.to]}
                            onClose={onClose}
                            onSelect={onSelect}
                            onDelete={() => {
                                onLinkDeleted(annotationPageNum, annotationId, link);
                            }}
                        />
                    ))}
                    {incomingLinks?.map((link) => (
                        <LinkRow
                            isEditable={isEditable}
                            key={link.to}
                            to={link.to}
                            icon={incomingLinkIcon}
                            annotationName={annotationNameById[link.to]}
                            onClose={onClose}
                            onSelect={onSelect}
                            onDelete={() => {
                                onLinkDeleted(link.page_num, link.to, {
                                    ...link,
                                    to: annotationId
                                });
                            }}
                        />
                    ))}
                </Panel>
            )}
            renderTarget={({ onClick, ...props }) => (
                <IconButton
                    {...props}
                    icon={linksIcon}
                    onClick={(event: Event) => {
                        event.stopPropagation();
                        onClick?.(event);
                    }}
                />
            )}
        />
    );
};
