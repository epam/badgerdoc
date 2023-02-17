import { Taxon } from 'api/typings';

export const getTaxonFullName = ({ name, parents }: Taxon): string => {
    const rootPath = parents?.map(({ name }: { name: string }) => name) || [];

    return [...rootPath, name].join('.');
};
