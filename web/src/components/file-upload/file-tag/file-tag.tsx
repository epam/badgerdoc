// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import React, { FC, useCallback } from 'react';
import { Tag, Text } from '@epam/loveship';

import { ReactComponent as otherFileIcon } from '@epam/assets/icons/common/file-file-24.svg';
import { ReactComponent as pdfIcon } from '@epam/assets/icons/common/file-file_pdf-24.svg';
import { ReactComponent as xlsIcon } from '@epam/assets/icons/common/file-file_excel-24.svg';
import { ReactComponent as jpgIcon } from '@epam/assets/icons/common/file-file_image-24.svg';

import styles from './file-tag.module.scss';

type FileTagProps = {
    file: File;
    onFileRemove(file: File): void;
};

export const FileTag: FC<FileTagProps> = ({ file, onFileRemove }) => {
    const onTagClear = useCallback(() => {
        onFileRemove(file);
    }, [file, onFileRemove]);
    const fileSpliter = '.';
    const fileName = file.name.split(fileSpliter);

    const caption = (
        <>
            <Text cx={styles['file-tag-text']}>{fileName.slice(0, -1).join(fileSpliter)}</Text>
            <Text cx={styles['file-tag-text']} fontSize="12" color="carbon">
                {fileName[fileName.length - 1]}, {(file.size! / 1024 ** 2).toFixed(2)} MB
            </Text>
        </>
    );

    const extension = fileName[fileName.length - 1].toLowerCase();
    const extToIcon: Record<string, { icon: any; color: string }> = {
        xls: {
            icon: xlsIcon,
            color: 'green'
        },
        jpg: {
            icon: jpgIcon,
            color: 'orange'
        },
        pdf: {
            icon: pdfIcon,
            color: 'red'
        }
    };

    let fileIcon = otherFileIcon;
    let fileColor = '';
    if (extToIcon[extension] && extToIcon[extension]) {
        fileIcon = extToIcon[extension].icon;
        fileColor = extToIcon[extension].color;
    }

    return (
        <Tag
            icon={fileIcon}
            caption={caption}
            onClear={onTagClear}
            size="30"
            cx={`${styles['file-tag']} ${styles[`file-tag--${fileColor}`]}`}
        ></Tag>
    );
};
