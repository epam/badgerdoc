import { Annotation } from '../../shared/components/annotator/typings';
import { LatestRevisionResponse, RevisionObjByUser, UserRevision } from './revisionTypes';

export function convertToUserRevisions(response: LatestRevisionResponse): UserRevision[] {
    const userRevisions: UserRevision[] = [];

    Object.values(response)
        .flat()
        .forEach((page) => {
            const { user_id, size, objs, revision, is_validated, date, pipeline, categories } =
                page;

            userRevisions.push({
                user_id,
                page_num: page.page_num,
                size,
                objs,
                revision,
                isValidated: is_validated,
                date,
                pipeline,
                categories
            });
        });

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

export function removeDuplicatesById(
    response: Record<string, Annotation[]>
): Record<string, Annotation[]> {
    const uniqResponseData = { ...response };
    const ids = new Set<number>();

    for (const key in uniqResponseData) {
        if (!hasProperty(uniqResponseData, key)) {
            continue;
        }

        uniqResponseData[key] = uniqResponseData[key].filter((annotation) => {
            if (ids.has(+annotation.id)) {
                return false;
            }
            ids.add(+annotation.id);
            return true;
        });
    }

    return uniqResponseData;
}

function hasProperty(response: Record<string, Annotation[]>, prop: string): boolean {
    return Object.prototype.hasOwnProperty.call(response, prop);
}
