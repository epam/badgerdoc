export type FileInfo = {
    file_name: string;
    id: number;
    action: string;
    status: boolean;
    message: string;
};

export type BondToDatasetResponse = FileInfo[];
