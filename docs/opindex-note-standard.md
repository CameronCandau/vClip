# OpIndex Note Standard

Use `OpIndex` notes for durable command references, not full AI chat archives.

## Required Structure

Each file should follow this pattern:

```markdown
# Topic Name

## Action-oriented plain English task
```bash
command here
```
```

Parser expectations:

- `#` creates the category shown in listings
- `##` creates the searchable task description
- fenced code blocks hold command content
- parseable languages are:
  - empty language
  - `bash`
  - `sh`
  - `shell`
  - `powershell`
  - `ps1`
  - `cmd`
  - `bat`
  - `batch`

## Authoring Rules

1. Start each file with a `#` category heading.
2. Put every reusable command under a `##` task heading.
3. Write task headings in plain English that describe the action.
4. Use one task heading per distinct intent.
5. Keep code blocks executable or nearly executable after placeholder replacement.
6. Use shell comments only for high-value caveats.
7. Prefer explicit placeholders like `<resource-group>` or `$IP`.
8. Avoid unsupported fenced languages for commands you expect `OpIndex` to parse.

## Good Example

```markdown
# Azure CLI

## Login with device code
```bash
az login --use-device-code
```

## List storage accounts in a resource group
```bash
az storage account list --resource-group <resource-group> --output table
```
```

## Bad Patterns

- code block without a `##` heading
- vague headings like `## Notes` or `## Misc`
- prose-only commands instead of fenced code blocks
- long narrative troubleshooting dumps
