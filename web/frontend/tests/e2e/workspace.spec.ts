import { expect, test, type Page, type Route } from '@playwright/test'

const extractionTag = 'deepseek-ocr-2'
const documentTitle = 'Glass Composition for High-Temperature Applications'
const extractionPageContent = `
  <div class="ocr_page" id="page_1" title="image &quot;page_1.png&quot;; bbox 0 0 1190 1683; ppageno 0; scan_res 144 144">
    <div class="ocr_carea" id="block_1_1" title="bbox 187 9 712 21">
      <p class="ocr_par" id="par_1_1" lang="eng" title="bbox 187 9 712 21" xml:lang="eng">
        <span class="ocr_textfloat" id="line_1_1" title="bbox 187 9 712 21; baseline 0 -5; x_size 20; x_descenders 5; x_ascenders 5">
          <span class="ocrx_word" id="word_1_1" title="bbox 187 9 289 18; x_wconf 91">REP-0337001</span>
          <span class="ocrx_word" id="word_1_2" title="bbox 296 9 329 18; x_wconf 82">v1.0</span>
          <span class="ocrx_word" id="word_1_3" title="bbox 347 9 396 18; x_wconf 82">Status:</span>
          <span class="ocrx_word" id="word_1_4" title="bbox 402 9 476 21; x_wconf 93">Approved</span>
          <span class="ocrx_word" id="word_1_5" title="bbox 494 9 568 21; x_wconf 93">Approved</span>
          <span class="ocrx_word" id="word_1_6" title="bbox 573 9 612 18; x_wconf 95">Date:</span>
          <span class="ocrx_word" id="word_1_7" title="bbox 619 9 635 18; x_wconf 96">12</span>
          <span class="ocrx_word" id="word_1_8" title="bbox 640 9 670 18; x_wconf 95">Dec</span>
          <span class="ocrx_word" id="word_1_9" title="bbox 675 9 712 18; x_wconf 95">2018</span>
        </span>
      </p>
    </div>
    <div class="ocr_carea" id="block_1_2" title="bbox 328 22 673 31">
      <p class="ocr_par" id="par_1_2" lang="eng" title="bbox 328 22 673 31" xml:lang="eng">
        <span class="ocr_header" id="line_1_2" title="bbox 328 22 673 31; baseline 0 0; x_size 20.366667; x_descenders 5.0916667; x_ascenders 5.0916667">
          <span class="ocrx_word" id="word_1_10" title="bbox 328 22 368 31; x_wconf 95">CofA</span>
          <span class="ocrx_word" id="word_1_11" title="bbox 374 22 376 31; x_wconf 95">|</span>
          <span class="ocrx_word" id="word_1_12" title="bbox 382 22 421 31; x_wconf 96">batch</span>
          <span class="ocrx_word" id="word_1_13" title="bbox 429 22 518 31; x_wconf 96">1000008665</span>
        </span>
      </p>
    </div>
    <div class="ocr_carea" id="block_1_4" title="bbox 98 111 409 130">
      <p class="ocr_par" id="par_1_3" lang="eng" title="bbox 98 111 409 130" xml:lang="eng">
        <span class="ocr_header" id="line_1_3" title="bbox 98 111 409 130; baseline -0.003 -5; x_size 33; x_descenders 6; x_ascenders 8">
          <span class="ocrx_word" id="word_1_17" title="bbox 98 111 244 127; x_wconf 96">Certificate</span>
          <span class="ocrx_word" id="word_1_18" title="bbox 254 111 282 127; x_wconf 96">of</span>
          <span class="ocrx_word" id="word_1_19" title="bbox 290 111 409 130; x_wconf 96">Analysis</span>
        </span>
      </p>
    </div>
  </div>
`

let latestExtractionPageContent = extractionPageContent

async function fulfillJson(route: Route, body: unknown) {
  await route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

async function mockAuth(page: Page) {
  await page.route('**/badgerdoc/user/me', async (route) => {
    await fulfillJson(route, {
      id: 1,
      username: 'playwright',
      first_name: 'Playwright',
      last_name: 'Tester',
      is_admin: true,
    })
  })
}

async function mockDziPublicPaths(page: Page) {
  await page.route('**/public/dzi/**', async (route) => {
    const proxiedUrl = route.request().url().replace('/public/dzi/', '/dzi/')
    await route.fulfill({
      status: 302,
      headers: {
        location: proxiedUrl,
      },
    })
  })
}

async function mockExtractionPages(page: Page) {
  await page.route('**/badgerdoc/document/1/extraction-page/latest/*', async (route) => {
    const requestedTag = new URL(route.request().url()).searchParams.get('tags')

    await fulfillJson(route, {
      count: requestedTag === extractionTag ? 1 : 0,
      next: null,
      previous: null,
      results:
        requestedTag === extractionTag
          ? [
              {
                id: 1,
                extraction_id: 45,
                page_number: 1,
                content: latestExtractionPageContent,
              },
            ]
          : [],
    })
  })
}

async function mockExtractionAcceptFlow(page: Page) {
  await page.route('**/badgerdoc/extraction/', async (route) => {
    if (route.request().method() !== 'POST') {
      await route.fallback()
      return
    }

    await fulfillJson(route, {
      id: 45,
      document_id: 1,
      status: 'Started',
      tags: [extractionTag],
    })
  })

  await page.route('**/badgerdoc/extraction-page/', async (route) => {
    const requestBody = route.request().postDataJSON() as {
      extraction_id: number
      page_number: number
      content: string
    }

    latestExtractionPageContent = requestBody.content

    await fulfillJson(route, {
      id: 1,
      extraction_id: requestBody.extraction_id,
      page_number: requestBody.page_number,
      content: requestBody.content,
    })
  })

  await page.route('**/badgerdoc/extraction/45/', async (route) => {
    if (route.request().method() !== 'PATCH') {
      await route.fallback()
      return
    }

    await fulfillJson(route, {
      id: 45,
      document_id: 1,
      status: 'Completed',
      tags: [extractionTag],
    })
  })
}

async function openExtractionWorkspace(page: Page) {
  await page.goto(`/ui/documents/1?tag=${extractionTag}`)
}

function firstEditorParagraph(page: Page) {
  return page.locator('.ProseMirror p').first()
}

async function appendToFocusedParagraph(page: Page, text: string) {
  await page.keyboard.type(text)
}

async function focusParagraphEnd(page: Page) {
  const paragraph = firstEditorParagraph(page)

  await paragraph.evaluate((node) => {
    const selection = window.getSelection()
    const range = document.createRange()

    range.selectNodeContents(node)
    range.collapse(false)
    selection?.removeAllRanges()
    selection?.addRange(range)
    ;(node as HTMLElement).focus()
  })
}

test.describe('workspace e2e', () => {
  test.beforeEach(async ({ page }) => {
    latestExtractionPageContent = extractionPageContent

    await mockAuth(page)
    await mockDziPublicPaths(page)
    await mockExtractionPages(page)
  })

  test('loads the extraction workspace tab with mocked browser data', async ({ page }) => {
    await page.goto('/ui/documents/1')

    await expect(page.getByRole('heading', { name: documentTitle })).toBeVisible()
    await expect(page.getByRole('tab', { name: 'Overview' })).toHaveAttribute(
      'aria-selected',
      'true'
    )

    await page.getByRole('tab', { name: 'Deepseek OCR 2' }).click()

    await expect(page).toHaveURL(/tag=deepseek-ocr-2/)
    await expect(page.getByRole('tab', { name: 'Deepseek OCR 2' })).toHaveAttribute(
      'aria-selected',
      'true'
    )
    await expect(page.locator('[data-block-id="block_1_1"]')).toBeVisible()
    await expect(page.locator('[data-block-id="block_1_4"]')).toBeVisible()
    await expect(page.locator('[data-block-id="block_1_1"] p')).toContainText('REP-0337001')
    await expect(page.locator('[data-block-id="block_1_4"] p')).toContainText(
      'Certificate of Analysis'
    )
  })

  test('edits extraction content and accepts the change through the real browser flow', async ({
    page,
  }) => {
    await mockExtractionAcceptFlow(page)
    await openExtractionWorkspace(page)

    const firstParagraph = firstEditorParagraph(page)
    await expect(firstParagraph).toContainText('REP-0337001')

    await focusParagraphEnd(page)
    await appendToFocusedParagraph(page, ' updated')

    await expect(page.getByRole('button', { name: 'Accept' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Revert' })).toBeVisible()
    await expect(firstParagraph).toContainText('updated')

    await page.getByRole('button', { name: 'Accept' }).click()

    await expect(page.getByRole('button', { name: 'Accept' })).toBeHidden()
    await expect(firstParagraph).toContainText('updated')
  })

  test('reverts extraction content changes in the real browser flow', async ({ page }) => {
    await openExtractionWorkspace(page)

    const firstParagraph = firstEditorParagraph(page)
    await expect(firstParagraph).toContainText('REP-0337001')

    await focusParagraphEnd(page)
    await appendToFocusedParagraph(page, ' updated')

    await expect(page.getByRole('button', { name: 'Accept' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Revert' })).toBeVisible()
    await expect(firstParagraph).toContainText('updated')

    await page.getByRole('button', { name: 'Revert' }).click()

    await expect(page.getByRole('button', { name: 'Accept' })).toBeHidden()
    await expect(page.getByRole('button', { name: 'Revert' })).toBeHidden()
    await expect(firstParagraph).toContainText('REP-0337001')
    await expect(firstParagraph).not.toContainText('updated')
  })
})
