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
import { useAddPluginMutation, useUpdatePluginMutation } from 'api/hooks/plugins';
import { PluginType } from 'api/typings';
import { useNotifications } from 'shared/components/notifications';

export const PluginModal: FC<IPluginProps> = ({ pluginValue, abort: onClose, ...props }) => {
    const { notifyError, notifySuccess } = useNotifications();
    const addPluginMutation = useAddPluginMutation();
    const updatePluginMutation = useUpdatePluginMutation();

    const getDefaultValues = (plugin: PluginType | undefined) => {
        const {
            url = '',
            name = '',
            menu_name = '',
            description = '',
            version = '',
            is_iframe = true
        } = plugin || {};

        return {
            name,
            menu_name,
            description,
            version,
            url,
            is_iframe
        };
    };

    const savePlugin = async (formValues: TPluginFormValues) => {
        try {
            if (pluginValue) {
                await updatePluginMutation.mutateAsync({
                    name: pluginValue.name,
                    menu_name: formValues.menu_name,
                    url: formValues.url
                });
                notifySuccess(<UiText>The plugin was successfully updated</UiText>);
            } else {
                await addPluginMutation.mutateAsync(formValues);
                notifySuccess(<UiText>The plugin was successfully added</UiText>);
            }
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
                                <LabeledInput label="Plugin Name" isRequired>
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
                        {!pluginValue && (
                            <FlexRow padding="24" vPadding="12">
                                <FlexCell grow={1}>
                                    <LabeledInput label="Description">
                                        <TextInput {...lens.prop('description').toProps()} />
                                    </LabeledInput>
                                </FlexCell>
                            </FlexRow>
                        )}
                        <FlexRow padding="24" vPadding="12">
                            <FlexCell grow={1}>
                                <LabeledInput label="Version" isRequired>
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
                                    <TextInput {...lens.prop('url').toProps()} />
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
