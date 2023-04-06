export const createTooltip = (isExtCov: boolean, notProcessedPages: number[]): string => {
    return isExtCov
        ? `Please wait for all annotators to finish their tasks`
        : `Please validate all page to finish task. Remaining pages: ${notProcessedPages?.join(
              ', '
          )}`;
};
