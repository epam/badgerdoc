# Extraction formats

Currently extraction pages expect to receive either:
- HTML - for general text structure description, to still support general text that is not tied to OCR.
- hOCR - for location-aware text description.

## hOCR
In order to support both TipTap and not reinvent the protocol for storing both location and style of both text and image elements hOCR format is used. See the latest specification at [hOCR - OCR Workflow and Output embedded in HTML](https://kba.github.io/hocr-spec/1.2/).

### Assumptions

Positioning - we will still use int-based coordinates for bbox, but `bbox ...` coordinates will be in range `[0, 1000]`.

Layout definition:
- `ocr_carea` will be the root "block" definition.
- Required capabilities: `ocr_photo`, `ocr_page`, `ocr_carea`, `ocr_par`, `ocr_line`, `ocrx_word`. [See documentation](https://kba.github.io/hocr-spec/1.2/#definition-capability).

ID assumptions:
- Each page has ID `page_<page number>`, such as `<div class="ocr_page" id="page_1" title="bbox 0 0 1190 1683; ppageno 0; scan_res 144 144">`, note `ppageno` is using 0-based indexing, compared to the IDs.
- Each element of hOCR page has ID in format `<tag name>_<page number>_<tag index>` for example for page number 4, 5th block we will have `block_4_5`
