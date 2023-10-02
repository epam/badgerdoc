// temporary_disabled_rules
/* eslint-disable @typescript-eslint/no-unused-vars */
import React from 'react';
import { Spinner } from '@epam/loveship';
import { PropsWithChildren } from 'react';

type PendingContentProps = PropsWithChildren<{
    loading: boolean;
    error?: null | Error;
}>;

export const PendingContent = ({ loading, error, children }: PendingContentProps) => {
    return (
        <>
            {Boolean(loading) && <Spinner color="sky" />}
            {Boolean(error) && !loading && 'Some error happened .....'}
            {!error && !loading && children}
        </>
    );
};
