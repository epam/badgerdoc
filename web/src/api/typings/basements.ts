export type SupportedArgument = {
    name: string;
    type: string;
    multiple: boolean;
    required: boolean;
};

export type Basement = {
    id: string;
    name: string;
    gpu_support: boolean;
    tenant?: string;
    created_by?: string;
    created_at?: string;
    supported_args?: SupportedArgument[];
};
