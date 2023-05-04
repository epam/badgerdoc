import { LatestRevisionObj, RevisionObjByUser, UserRevision } from './revisionTypes';

export function convertToRevisionByUserArray(sourceObj: LatestRevisionObj): UserRevision[] {
    const userRevisions: UserRevision[] = [];

    for (const page_num in sourceObj) {
        const pages = sourceObj[page_num];

        for (const page of pages) {
            const { user_id, size, objs, revision, is_validated, date, pipeline, categories } =
                page;

            userRevisions.push({
                user_id,
                page_num: parseInt(page_num),
                size,
                objs,
                revision,
                isValidated: is_validated,
                date,
                pipeline,
                categories
            });
        }
    }

    return userRevisions;
}

export function deleteAllRevisionByUser(
    sourceObj: RevisionObjByUser,
    user_id?: string
): RevisionObjByUser {
    if (!user_id) return sourceObj;

    const result: RevisionObjByUser = { ...sourceObj };
    delete result[user_id];

    return result;
}

export function getRevisionByUser(
    sourceObj: RevisionObjByUser,
    user_id?: string
): RevisionObjByUser {
    if (!user_id) return {};
    const result: RevisionObjByUser = {};

    if (user_id in sourceObj) {
        result[user_id] = sourceObj[user_id];
    }

    return result;
}
