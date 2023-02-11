# Test data

Example inputs to the CLI

| Ex#     | `.tsv`                                                              | `.json`                                                                          | Expect |
|---------|---------------------------------------------------------------------|----------------------------------------------------------------------------------|--------|
| 1       | invalid, non-unique combinations of `participant` and `session` IDs | valid, has `IsAbout` annotations for `participant` and `session` ID columns      | fail   |
| 2       | valid, unique `participant` and `session` IDs                       | same as example 1                                                                | pass   |
| 3       | same as example 2                                                   | valid BIDS data dictionary, BUT: does not contain Neurobagel `"Annotations"` key | fail   |
| 4       | valid, has additional columns not described in `.json`              | same as example 1                                                                | pass   |
| 5       | valid, has additional unique value, not documented in `.json`       | same as example 1                                                                | fail   |
| 6       | valid, same as example 5. hass annotation tool columns              | valid, contains `"MissingValues"` attribute for categorical variable             | pass   |
| invalid | valid, only exists to be used together with the (invalid) .json     | invalid, missing the `"TermURL"` attribute for identifiers                       | fail   |
| 7       | has fewer columns than are annotated in `.json`                     | same as example 1                                                                | fail   |
| 8       | valid, based on ex2 has multiple participant_id columns             | valid, based on ex2 multiple participant_id column annotations                   | fail*  |

`* this is expected to fail until we enable multiple participant_ID handling`.