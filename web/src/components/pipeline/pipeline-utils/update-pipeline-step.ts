import { Step } from 'api/typings';

export const updatePipelineStep = (
    steps: Step[],
    stepId: string,
    replacer: (step: Step) => Step
): Step[] => {
    if (!steps.length) {
        return steps;
    }
    return steps.map((step) => {
        if (step.id === stepId) {
            return replacer(step);
        }
        return {
            ...step,
            steps: updatePipelineStep(step.steps ?? [], stepId, replacer)
        };
    });
};
