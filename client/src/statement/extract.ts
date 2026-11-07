import { getDocument, PasswordResponses } from 'pdfjs-dist/legacy/build/pdf.mjs'
import { IncorrectPasswordError, PasswordRequiredError } from './errors'
import type { PageText } from './types'

export async function extractPages(pdf: ArrayBuffer, password?: string): Promise<PageText[]> {
  const loading = getDocument({ data: new Uint8Array(pdf.slice(0)), password })
  const document = await loading.promise.catch((error: unknown) => {
    throw translatePasswordError(error)
  })

  try {
    const pages: PageText[] = []
    for (let number = 1; number <= document.numPages; number++) {
      const { items } = await (await document.getPage(number)).getTextContent()
      pages.push(
        items.flatMap((item) =>
          'str' in item && item.str.trim() ? [{ text: item.str, x: item.transform[4], y: item.transform[5] }] : [],
        ),
      )
    }
    return pages
  } finally {
    await loading.destroy()
  }
}

function translatePasswordError(error: unknown): unknown {
  if (!(error instanceof Error) || error.name !== 'PasswordException') return error
  const { code } = error as Error & { code: number }
  return code === PasswordResponses.INCORRECT_PASSWORD
    ? new IncorrectPasswordError('That password did not open this file.')
    : new PasswordRequiredError('This file is password protected.')
}
