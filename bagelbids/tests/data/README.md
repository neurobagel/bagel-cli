# Test data

Example inputs to the CLI

- example1
- example2
  - .tsv
    - is valid
    - has unique participant and session ID
  - .json
    - is valid Neurobagel .json
    - has tags for participant and session ID
- example3
  - .tsv
    - same as example2
  - .json
    - is valid as BIDS
    - BUT: is not valid as Neurobagel (no `"Annotations"` field)