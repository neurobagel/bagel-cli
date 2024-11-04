# Test data

## Example inputs to the `bagel pheno` CLI command

| Example name | `.tsv` | `.json` | Expect |
| ----- | ----- | ----- | ----- |
| 1 | invalid, non-unique combinations of `participant` and `session` IDs | valid, has `IsAbout` annotations for `participant` and `session` ID columns | fail |
| 2 | valid, unique `participant` and `session` IDs | same as example 1 | pass |
| 3 | same as example 2 | valid BIDS data dictionary, BUT: does not contain Neurobagel `"Annotations"` key | fail |
| 4 | valid, has additional columns not described in `.json` | same as example 1 | pass |
| 5 | valid, has additional unique value, not documented in `.json` | same as example 1 | fail |
| 6 | valid, same as example 5. has annotation tool columns | valid, contains `"MissingValues"` attribute for categorical variable | pass |
| invalid | valid, only exists to be used together with the (invalid) .json | invalid, missing the `"TermURL"` attribute for identifiers | fail |
| 7 | has fewer columns than are annotated in `.json` | same as example 1 | fail |
| 8 | valid, based on ex2 has multiple participant_id columns | valid, based on ex2 multiple participant_id column annotations | fail* |
| 9 | invalid, based on example 6 but contains an unannotated value for `group` | valid, based on example 6 | fail |
| 10 | valid, same as example 6 | valid, based on example 6 but contains extra `"MissingValues"` not found in the .tsv | pass, with warning |
| 11 | invalid, ex 6 with missing entries in `participant_id` and `session_id` columns | valid, based on example 6 | fail |
| 12 | Valid, same as example 2 | Valid, based on example 2 but missing BIDS "Levels" attribute for group column | Pass, with warning |
| 13 | Valid, same as example_synthetic | Valid, based on example_synthetic but with mismatched levels for group column | Pass, with warning |
| 14 | Valid, same as example 2 | Valid, based on example 2, but with an extra column annotation without Neurobagel | Pass |
| 15 | Valid, same as example 2 | Invalid, based on example 2, but participant ID column lacks Neurobagel annotations | Fail |
| 16 | Invalid, same as example2.csv, but with a sneaky .tsv file ending | Valid, same as example2 | fail |
| 17 | Valid, contains data for three subjects, but no session column | Same as example 2 JSON, without `session_id` column | pass |
| 18 | Invalid, example2.tsv without `session_id` column, so there are non-unique participant rows | Same as example 2 JSON, without session_id column | fail |
| 19 | Example with two columns about diagnosis | Valid | pass |
| 20 | Valid, based on example 19 but contains multiple annotated columns about age and sex | Valid | pass |
| 21 | Valid, based on example 2 but contains a dash in a column name | Valid | pass |
| iso88591 | invalid, ISO-8859-1 encoded and contains French characters in the age column | invalid, ISO-8859-1 encoded and contains French characters in the age column | fail |
| invalid_json | - | not valid JSON, contains trailing comma after `group` key-value pair | fail |

`* this is expected to fail until we enable multiple participant_ID handling`.

## Example inputs to the `bagel derivatives` command
Designed to work with `.jsonld` files from the [Neurobagel reference example dataset](https://github.com/neurobagel/neurobagel_examples).

Example file `proc_status`... | Description | Expected result
----- | ----- | -----
_synthetic.tsv | Captures a subset of subject-sessions represented in the BIDS examples synthetic dataset | Pass
_synthetic.csv | Same as proc_status_synthetic.csv, but is a CSV file | Fail
_unique_subs.tsv | Includes subjects not found in the phenotypic dataset | Fail
_incomplete.tsv | Has a missing value in the `bids_participant_id` column | Fail
_unique_sessions.csv | Includes a unique subject-session (`sub-01`, `ses-03`) not found in the synthetic dataset | Pass
_missing_sessions.tsv | One subject (`sub-02`) is missing all session labels | Pass
_no_bids_sessions.tsv | Has session labels in all rows for `session_id`, but no values in `bids_session_id` column | Pass


## Example expected CLI outputs
You can find example expected CLI outputs [here](https://github.com/neurobagel/neurobagel_examples).