# Test data

Example inputs to the CLI

| Example name | `.tsv`                                                                          | `.json`                                                                              | Expect             |
| ------------ | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------ |
| 1            | invalid, non-unique combinations of `participant` and `session` IDs             | valid, has `IsAbout` annotations for `participant` and `session` ID columns          | fail               |
| 2            | valid, unique `participant` and `session` IDs                                   | same as example 1                                                                    | pass               |
| 3            | same as example 2                                                               | valid BIDS data dictionary, BUT: does not contain Neurobagel `"Annotations"` key     | fail               |
| 4            | valid, has additional columns not described in `.json`                          | same as example 1                                                                    | pass               |
| 5            | valid, has additional unique value, not documented in `.json`                   | same as example 1                                                                    | fail               |
| 6            | valid, same as example 5. has annotation tool columns                           | valid, contains `"MissingValues"` attribute for categorical variable                 | pass               |
| invalid      | valid, only exists to be used together with the (invalid) .json                 | invalid, missing the `"TermURL"` attribute for identifiers                           | fail               |
| 7            | has fewer columns than are annotated in `.json`                                 | same as example 1                                                                    | fail               |
| 8            | valid, based on ex2 has multiple participant_id columns                         | valid, based on ex2 multiple participant_id column annotations                       | fail*              |
| 9            | invalid, based on example 6 but contains an unannotated value for `group`       | valid, based on example 6                                                            | fail               |
| 10           | valid, same as example 6                                                        | valid, based on example 6 but contains extra `"MissingValues"` not found in the .tsv | pass, with warning |
| 11           | invalid, ex 6 with missing entries in `participant_id` and `session_id` columns | valid, based on example 6                                                            | fail               |
| 12           | Valid, same as example 2                                                        | Valid, based on example 2 but missing BIDS "Levels" attribute for group column       | Pass, with warning |
| 13           | Valid, same as example_synthetic                                                | Valid, based on example_synthetic but with mismatched levels for group column        | Pass, with warning |
| 14           | Valid, same as example 2                                                        | Valid, based on example 2, but with an extra column annotation without Neurobagel    | Pass               |
| 15           | Valid, same as example 2                                                        | Invalid, based on example 2, but participant ID column lacks Neurobagel annotations  | Fail               |
| 16           | Invalid, same as example2.csv, but with a sneaky .tsv file ending               | Valid, same as example2                                                              | fail               |
| 17 | Valid, contains data for three subjects, but no session column | Same as example 2 JSON, without `session_id` column | pass |
| 18 | Invalid, example2.tsv without `session_id` column, so there are non-unique participant rows | Same as example 2 JSON, without session_id column | fail |
| 19 | Example with two columns about diagnosis | Valid | pass

`* this is expected to fail until we enable multiple participant_ID handling`.

## Example expected CLI outputs
You can find example expected CLI outputs [here](https://github.com/neurobagel/neurobagel_examples).