import { Panel, ModalHeader, ModalFooter, FlexRow, FlexSpacer, Button, Text } from '@epam/loveship';
import React, { ReactElement, useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import { Rnd } from 'react-rnd';
import { Bound } from 'shared';
import Latex from 'react-latex';
import { ExternalViewerPopupProps } from 'api/typings/annotations';
import { StandaloneStructServiceProvider } from 'ketcher-standalone';
import { Editor, ButtonsConfig } from 'ketcher-react';
import { ALL_BUTTONS } from './buttons-config';
import { Ketcher } from 'ketcher-core';
import 'ketcher-react/dist/index.css';
import styles from './external-viewer-popup.module.scss';

const structServiceProvider = new StandaloneStructServiceProvider();
import { CategoryDataAttrType } from 'api/typings';

const addLaTex = () => {
    let link = document.createElement('link');
    link.href = '//cdnjs.cloudflare.com/ajax/libs/KaTeX/0.9.0/katex.min.css';
    link.rel = 'stylesheet';
    document.head.appendChild(link);
};

const getHiddenButtonsConfig = (hiddenButtons: string[] | null = null): ButtonsConfig => {
    if (!hiddenButtons) return {};

    return hiddenButtons.reduce((acc: any, button) => {
        if (button) acc[button] = { hidden: true };

        return acc;
    }, {});
};

const setUpContent = (value: string, type: CategoryDataAttrType) => {
    switch (type) {
        case 'latex':
            addLaTex();
            return <Latex>{`$$${value}$$`}</Latex>;
        case 'molecule':
            return (
                <Editor
                    staticResourcesUrl={process.env.PUBLIC_URL}
                    structServiceProvider={structServiceProvider}
                    onInit={(ketcherObj: Ketcher) => {
                        ketcherObj.setMolecule(value);
                    }}
                    errorHandler={(e) => console.log(e)}
                    buttons={getHiddenButtonsConfig(ALL_BUTTONS)}
                />
            );
        default:
            return <Text color="carbon"> Sorry, the provided data is unrecognized </Text>;
    }
};

const defaultWidth = window.innerWidth < 900 ? window.innerWidth : 900;
const defaultHeight = window.innerHeight < 800 ? window.innerHeight : 800;
const defaultViewerBound: Bound = {
    width: defaultWidth,
    height: defaultHeight,
    x: -(defaultWidth / 2),
    y: -(defaultHeight / 2)
};

export default function ExternalViewerPopup({
    onClose,
    valueAttr,
    typeAttr,
    nameAttr
}: ExternalViewerPopupProps) {
    const [externalViewerBound, setExternalViewerBound] = useState<Bound>(defaultViewerBound);
    const [content, setContent] = useState<ReactElement>(<></>);

    const popupContainer = document.getElementById('popup');

    useEffect(() => setContent(setUpContent(valueAttr, typeAttr)), []);

    return (
        popupContainer &&
        ReactDOM.createPortal(
            <>
                <div className={styles['rnd-wrapper']}>
                    <Rnd
                        size={{
                            width: externalViewerBound.width,
                            height: externalViewerBound.height
                        }}
                        position={{ x: externalViewerBound.x, y: externalViewerBound.y }}
                        onDragStop={(e, d) => {
                            setExternalViewerBound((prev: Bound) => ({ ...prev, x: d.x, y: d.y }));
                        }}
                        onResizeStop={(e, direction, ref, delta, position) => {
                            setExternalViewerBound({
                                width: ref.clientWidth,
                                height: ref.clientHeight,
                                ...position
                            });
                        }}
                        className={styles['rnd-popup']}
                        dragHandleClassName={styles['draggable']}
                    >
                        <Panel background="white" cx={styles['rnd-panel']}>
                            <ModalHeader
                                title={`${nameAttr} (${typeAttr})`}
                                cx={styles['draggable']}
                                onClose={() => onClose()}
                            />

                            <FlexRow padding="24" vPadding="12" cx={styles['rnd-content']}>
                                {content}
                            </FlexRow>
                            <ModalFooter>
                                <FlexSpacer />
                                <Button
                                    cx={styles['rnd-button']}
                                    caption="Close"
                                    onClick={() => onClose()}
                                />
                            </ModalFooter>
                        </Panel>
                    </Rnd>
                </div>
            </>,
            popupContainer
        )
    );
}
