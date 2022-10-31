import React, { CSSProperties, FC, useMemo } from 'react';
import { Token } from '../../components/page-token';
import { PageToken } from '../../typings';
import uniq from 'lodash/uniq';

type TokensLayerProps = {
    tokens: PageToken[];
    scale: number;
    tokenStyle?: Pick<CSSProperties, 'background' | 'opacity'>;
};

const defaultTokenStyle = {
    opacity: 0.2,
    background: 'blue'
};

export const TokensLayer: FC<TokensLayerProps> = ({
    tokens,
    scale,
    tokenStyle = defaultTokenStyle
}) => {
    const scaledTokens = useMemo(() => {
        return (uniq(tokens) || []).map((t) => ({
            ...t,
            x: t.x * scale,
            y: t.y * scale,
            width: t.width * scale,
            height: t.height * scale
        }));
    }, [tokens, scale]);

    return (
        <>
            {scaledTokens.map((token) => (
                <Token key={token.id} token={token} tokenStyle={tokenStyle} />
            ))}
        </>
    );
};
