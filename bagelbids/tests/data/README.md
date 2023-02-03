# Test data

Example inputs to the CLI

- example1
  - .tsv
    - invalid
    - has duplicate participantID-sessionID pairs
  - .json
    - is valid Neurobagel .json
    - has tags for participant and session ID
- example2
  - .tsv
    - is valid
    - has unique participant and session ID
  - .json
    - same as example1
- example3
  - .tsv
    - same as example2
  - .json
    - is valid as BIDS
    - BUT: is not valid as Neurobagel (no `"Annotations"` field)