import { AxiosError } from 'axios'

type BadgerdocAPIErrorResponse = {
  [K in string]?: K extends 'error' ? string : string[]
}

export const getErrorMessageFromResponse = (
  error?: AxiosError<BadgerdocAPIErrorResponse> | Error
): string => {
  const responseData = error instanceof AxiosError ? error?.response?.data || {} : {}

  return (
    responseData?.error ||
    responseData?.message ||
    Object.getOwnPropertyNames(responseData)
      .reduce((errorMessages, dataField): string[] => {
        const fieldErrors = responseData[dataField]?.join?.(' ')
        return [...errorMessages, fieldErrors]
      }, [])
      ?.filter((message) => !!message)
      ?.join(' ') ||
    (error as Error)?.message ||
    'BadgerDoc API error'
  )
}
