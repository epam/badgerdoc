// // temporary_disabled_rules
// /* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-redeclare */
import { FC } from 'react';
import {
    Button,
    Checkbox,
    FlexCell,
    FlexRow,
    FlexSpacer,
    LabeledInput,
    ModalBlocker,
    ModalFooter,
    ModalHeader,
    ModalWindow,
    Panel,
    ScrollBars,
    Text as UiText,
    TextInput,
    useForm
} from '@epam/loveship';
import { IPluginProps, TPluginFormValues } from './types';
import { getError } from 'shared/helpers/get-error';
import { useAddPluginMutation, useUpdatePluginMutation, usePlugins } from 'api/hooks/plugins';
import { useNotifications } from 'shared/components/notifications';
import { getDefaultValues, isValidUrl } from './utils';

const VALIDATION_MESSAGE = 'Please enter a valid URL starting with http://';

export const PluginModal: FC<IPluginProps> = ({ pluginValue, abort: onClose, ...props }) => {
    const { notifyError, notifySuccess } = useNotifications();
    const addPluginMutation = useAddPluginMutation();
    const { mutateAsync: updatePluginMutate } = useUpdatePluginMutation();
    const { refetch: refetchPlugins } = usePlugins();

    const savePlugin = async (formValues: TPluginFormValues) => {
        if (!isValidUrl(formValues.url)) {
            notifyError(<UiText>{VALIDATION_MESSAGE}</UiText>);
            return;
        }

        try {
            if (pluginValue) {
                await updatePluginMutate({
                    id: Number(pluginValue.id),
                    data: {
                        menu_name: formValues.menu_name,
                        description: formValues.description,
                        url: formValues.url,
                        is_iframe: formValues.is_iframe
                    }
                });
                notifySuccess(<UiText>The plugin was successfully updated</UiText>);
            } else {
                await addPluginMutation.mutateAsync(formValues);
                notifySuccess(<UiText>The plugin was successfully added</UiText>);
            }
            await refetchPlugins();
            onClose();
        } catch (err: any) {
            notifyError(<UiText>{getError(err)}</UiText>);
        }
    };

    const { lens, save } = useForm({
        onSave: savePlugin,
        value: getDefaultValues(pluginValue)
    });

    const title = pluginValue ? 'Edit plugin' : 'Add new plugin';

    return (
        <ModalBlocker disallowClickOutside blockerShadow="dark" {...props} abort={onClose}>
            <ModalWindow>
                <Panel background="white">
                    <ModalHeader title={title} />
                    <ScrollBars>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Plugin Name" isRequired={!pluginValue}>
                                    <TextInput
                                        {...lens.prop('name').toProps()}
                                        isDisabled={!!pluginValue}
                                    />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Menu Name" isRequired>
                                    <TextInput {...lens.prop('menu_name').toProps()} />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Description">
                                    <TextInput {...lens.prop('description').toProps()} />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Version" isRequired={!pluginValue}>
                                    <TextInput
                                        {...lens.prop('version').toProps()}
                                        isDisabled={!!pluginValue}
                                    />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="URL" isRequired>
                                    <TextInput
                                        {...lens.prop('url').toProps()}
                                        isInvalid={
                                            !!lens.prop('url').toProps().value &&
                                            !isValidUrl(lens.prop('url').toProps().value)
                                        }
                                        placeholder="http://example.com/plugin"
                                    />
                                </LabeledInput>
                            </FlexCell>
                        </FlexRow>
                        {!pluginValue && (
                            <FlexRow padding="24" vPadding="12">
                                <FlexCell grow={1}>
                                    <Checkbox
                                        label="Is Iframe Plugin?"
                                        {...lens.prop('is_iframe').toProps()}
                                    />
                                </FlexCell>
                            </FlexRow>
                        )}
                    </ScrollBars>
                    <ModalFooter>
                        <FlexSpacer />
                        <Button fill="white" caption="Cancel" onClick={onClose} />
                        <Button onClick={save} caption={pluginValue ? 'Update' : 'Save'} />
                    </ModalFooter>
                </Panel>
            </ModalWindow>
        </ModalBlocker>
    );
};
