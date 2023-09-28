// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React from 'react';
import type { PageToken, TokenStyle } from '../../typings';
import styles from './page-token.module.scss';

type TokenProps = {
    token: PageToken;
    tokenStyle?: TokenStyle;
};

export const Token = ({ token, tokenStyle }: TokenProps) => {
    return (
        <span
            className={styles['page-token']}
            style={{
                left: token.x,
                top: token.y,
                width: token.width,
                height: token.height,
                ...tokenStyle,
                ...token.style
            }}
        ></span>
    );
};
