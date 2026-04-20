import { describe, it, expect } from 'vitest'
import { AxiosError, AxiosResponse } from 'axios'
import { getErrorMessageFromResponse } from './get-error-message-from-response'

describe('API Error Message formatter', () => {
  it('should return correct message WHEN response body contains "error" field', () => {
    const expectedErrorMessage =
      'Failed to upload document: An error occurred (NoSuchBucket) when calling the CreateMultipartUpload operation: The specified bucket does not exist'

    const mockError = new AxiosError('Request failed', 'ECONNABORTED', undefined, undefined, {
      data: {
        error: expectedErrorMessage,
      },
      status: 500,
      statusText: 'Internal Server Error',
    } as AxiosResponse)
    expect(getErrorMessageFromResponse(mockError)).toBe(expectedErrorMessage)
  })

  it('should return correct message WHEN response body contains "message" field', () => {
    const expectedErrorMessage =
      'Failed to upload document: An error occurred (NoSuchBucket) when calling the CreateMultipartUpload operation: The specified bucket does not exist'

    const mockError = new AxiosError('Request failed', 'ECONNABORTED', undefined, undefined, {
      data: {
        message: expectedErrorMessage,
      },
      status: 500,
      statusText: 'Internal Server Error',
    } as AxiosResponse)
    expect(getErrorMessageFromResponse(mockError)).toBe(expectedErrorMessage)
  })

  it('should return correct message WHEN response contains message', () => {
    const expectedErrorMessage = 'Request failed'

    const mockError = new AxiosError(expectedErrorMessage, 'ECONNABORTED', undefined, undefined, {
      status: 500,
      statusText: 'Internal Server Error',
    } as AxiosResponse)
    expect(getErrorMessageFromResponse(mockError)).toBe(expectedErrorMessage)
  })

  it('should return correct message WHEN response body contains per-field error messages', () => {
    const fileErrorMessage = 'File name must not exceed 100 characters (got 107).'
    const metadataErrorMessage = 'Metadata validation failed: valid json expected.'

    const mockError = new AxiosError('Request failed', 'ECONNABORTED', undefined, undefined, {
      data: {
        file: [fileErrorMessage],
        metadata: [metadataErrorMessage],
      },
      status: 400,
      statusText: 'Bad Request',
    } as AxiosResponse)
    expect(getErrorMessageFromResponse(mockError)).toBe(
      `${fileErrorMessage} ${metadataErrorMessage}`
    )
  })

  it('should return correct message WHEN non-API error is handled', () => {
    const expectedErrorMessage = 'Failed to prepare data for request'
    const mockError = new Error(expectedErrorMessage)

    expect(getErrorMessageFromResponse(mockError)).toBe(expectedErrorMessage)
  })

  it('should return fallback WHEN no info about the error is available', () => {
    expect(getErrorMessageFromResponse()).toBe('BadgerDoc API error')
  })
})
