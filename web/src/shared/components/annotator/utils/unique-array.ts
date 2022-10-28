export const arrayUniqueByKey = (array: any[], key: string) =>
    Array.from(new Map(array.map((item) => [item[key], item])).values());
