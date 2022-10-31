// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import React from 'react';
import '@testing-library/jest-dom';

jest.setTimeout(30000);

const Document = ({ onLoadSuccess = (pdf = { numPages: 1 }) => pdf.numPages }) => {
    return <div>{onLoadSuccess({ numPages: 1 })}</div>;
};

Document.propTypes = {
    onLoadSuccess: () => {}
};

const Page = () => <div>def</div>;

jest.mock('react-pdf', () => ({
    pdfjs: { GlobalWorkerOptions: { workerSrc: 'abc' } },
    Document,
    Outline: null,
    Page
}));
