# XLSX-Ray workbook diff

- **Before:** `examples/generated/before.xlsx`
- **After:** `examples/generated/after.xlsm`
- **Changes:** 9
- **Highest risk:** `high`

| Risk | Category | Subject | Before | After | Why it matters | Formula impact leads (Direct formula dependents and static evidence) |
| --- | --- | --- | --- | --- | --- | --- |
| `high` | `data_validation_changed` | `Assumptions` | `["{\"attributes\":{\"formula1\":\"1\",\"formula2\":\"100\",\"operator\":\"between\",\"sqref\":\"A1\",\"type\":\"whole\"},\"children\":[],\"tag\":\"dataValidation\"}"]` | `[]` | A data-validation rule was removed or replaced. | — |
| `high` | `defined_name_changed` | `InputLimit` | `Inputs!$A$1` | `Assumptions!$A$1` | A defined name reference changed. | `Model!C2` — `defined_name` via `InputLimit` → `Assumptions!$A$1`<br>`Model!C2` — `defined_name` via `InputLimit` → `Inputs!$A$1` |
| `high` | `external_link_added` | `https://example.invalid/external.xlsx` | — | `https://example.invalid/external.xlsx` | An external workbook link was introduced. | — |
| `high` | `formula_changed` | `Model!B2` | `=Inputs!A1*2` | `=Assumptions!A1*2` | A formula changed; formula results are not calculated by XLSX-Ray. | — |
| `high` | `vba_presence_changed` | `xl/vbaProject.bin` | `False` | `True` | VBA package presence changed. XLSX-Ray never executes VBA. | — |
| `high` | `workbook_protection_changed` | `workbook` | `{"lockStructure": "1"}` | `{}` | Workbook protection was removed. | — |
| `high` | `worksheet_protection_changed` | `Assumptions` | `{"sheet": "1"}` | `{}` | Worksheet protection was removed. | — |
| `medium` | `sheet_renamed` | `Inputs` | `Inputs` | `Assumptions` | A worksheet name changed while its OOXML worksheet part was retained. | — |
| `low` | `cell_value_changed` | `Assumptions!A1` | `10` | `12` | A non-formula cell value changed. | `Model!B2` — `direct_a1` via `Assumptions!A1` → `Assumptions!A1`<br>`Model!C2` — `defined_name` via `InputLimit` → `Assumptions!$A$1` |

> XLSX-Ray is read-only and does not calculate formulas, execute VBA, or follow external links. Formula impact leads are static, evidence-only review hints; they are not a complete dependency graph or calculated-outcome claim.
