# Trigger Workflow

The endpoint `POST /badgerdoc/workflow-registry/trigger/{workflow_registry_id}` triggers a new workflow execution.

## Example Request

```json
{
  "document_id": 123,
  "llm_params": "User prompt with link to [/badgerdoc/document/{document_id}/extraction/{extraction_id}/page/{num}/(//div[@id='block_1_1'])]"
}
```

### Parameters

- `document_id` - The ID of the document to which this extraction will be linked
- `llm_params` - The prompt containing special link syntax to reference documents, pages, or extractions

Some models may ignore the user prompt; however, the back-end will still parse the `xpath` to locate the exact document/page/block.

## How to Create Prompts

Special symbols `[...]` in `llm_params` indicate a link to a document, document page, or extraction. **Important:** The user must have access to the referenced document, or the input will be ignored.

### Whole Document

If the model needs to receive a whole document without any prompt:

```json
{
  "document_id": 123,
  "llm_params": "[/badgerdoc/document/{document_id}/]"
}
```

- `[/badgerdoc/document/{document_id}/]` - Instructs the model to download the whole document and run extraction on it (in most cases, page by page)

### Single Page

If the model needs to receive a single document page without any prompt:

```json
{
  "document_id": 123,
  "llm_params": "[/badgerdoc/document/{document_id}/page/{num}]"
}
```

- `[/badgerdoc/document/{document_id}/page/{num}]` - Instructs the model to download the specified page and run extraction on it

### Multiple Pages

If the model needs to receive multiple pages without any prompt:

```json
{
  "document_id": 123,
  "llm_params": "[/badgerdoc/document/{document_id}/page/{num_1}][/badgerdoc/document/{document_id}/page/{num_2}]"
}
```

- `[/badgerdoc/document/{document_id}/page/{num_1}][/badgerdoc/document/{document_id}/page/{num_2}]` - Instructs the model to download the listed pages and run extraction on them

### Extraction

If the model needs to receive an extraction without any prompt:

```json
{
  "document_id": 123,
  "llm_params": "[/badgerdoc/document/{document_id}/extraction/{extraction_id}/page/{num}/]"
}
```

- `[/badgerdoc/document/{document_id}/extraction/{extraction_id}/page/{num}/]` - Instructs the model to download the extraction and run extraction on it

### Extraction Block with XPath

If the model needs to receive a specific extraction block without any prompt:

```json
{
  "document_id": 123,
  "llm_params": "[/badgerdoc/document/{document_id}/extraction/{extraction_id}/page/{num}/(//div[@id='block_1_1'])]"
}
```

- `[/badgerdoc/document/{document_id}/extraction/{extraction_id}/page/{num}/(//div[@id='block_1_1'])]` - Instructs the model to download the extraction and locate the exact block using the XPath `//div[@id='block_1_1']`, then run extraction on it

### Custom Prompts

You can use custom prompts with or without document links:

**With document links:**

```json
{
  "document_id": 123,
  "llm_params": "Extract all tables from this document: [/badgerdoc/document/{document_id}/]"
}
```

**Without document links:**

```json
{
  "document_id": 123,
  "llm_params": "Extract all tables from the provided document"
}
```

The model will receive your custom prompt and, if included, the referenced document content.

## How Prompts are Compiled

Badgerdoc processes prompts as follows:

1. **Parse** - The system searches for `[/badgerdoc/` occurrences in the prompt
2. **Validate** - It checks if the user has access to the referenced document
3. **Filter** - If the user doesn't have access, the reference is removed from the prompt
4. **Prepare** - Badgerdoc prepares an extended request to the extraction model with the validated content
