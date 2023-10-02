// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import { useAsyncDataSource } from '@epam/uui';
import { useEffect, useMemo, useRef } from 'react';

export const useAsyncSourceTable = <TData, TId>(
    isFetching: boolean,
    data: TData[],
    ...deps: unknown[]
) => {
    const deferred = useRef<{
        promise: Promise<TData[]>;
        resolver: (data: TData[]) => void;
    } | null>();

    useEffect(() => {
        if (typeof isFetching === 'boolean' && !isFetching) {
            deferred.current?.resolver(data);
            deferred.current = null;
        }
    }, [isFetching]);

    const dataSource = useAsyncDataSource<TData, TId, unknown>(
        {
            api: () => {
                if (deferred.current) {
                    return deferred.current.promise;
                }
                let resolver: (data: TData[]) => void;

                const promise = new Promise<TData[]>((resolve) => {
                    resolver = resolve;
                });

                deferred.current = { resolver: resolver!, promise };
                return deferred.current!.promise;
            }
        },
        deps
    );

    return useMemo(() => ({ dataSource }), deps);
};
