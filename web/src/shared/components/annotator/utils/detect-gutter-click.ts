export const possiblyClickedOnTableGutter = (target: HTMLElement): boolean => {
    return target.classList[0]?.includes('gutter') || target.classList[0]?.includes('gutter-core');
};
