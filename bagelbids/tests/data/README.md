# Test data

Example inputs to the CLI

- example1: duplicate IDs in .tsv -> fail
  - .tsv
    - invalid
    - has duplicate participantID-sessionID pairs
  - .json
    - is valid Neurobagel .json
    - has tags for participant and session ID
- example2: good data -> pass
  - .tsv
    - is valid
    - has unique participant and session ID
  - .json
    - same as example1
- example3: good data, but no annotations in .json -> fail
  - .tsv
    - same as example2
  - .json
    - is valid as BIDS
    - BUT: is not valid as Neurobagel (no `"Annotations"` field)
- example4: tsv has additional columns -> pass
  - .tsv
    - is valid
    - BUT: has more columns than are annotated in the .json
  - .json
    - same as example 1
