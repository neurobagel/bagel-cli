#!/bin/bash

CLI_COMMAND="$1"
INPUT_BIDS_DIR="/data/bids"

if [ "$CLI_COMMAND" == "bids" ]; then
    if [ ! -d "$INPUT_BIDS_DIR" ]; then
        echo "ERROR: Required directory $INPUT_BIDS_DIR for the bagel bids command not found inside the container."
        echo "Please ensure you have mounted the BIDS dataset directory on your host machine to /data/bids inside the container."
        echo "EXAMPLE (Docker):"
        echo "docker run --rm -v /PATH/TO/JSONLD/DIR:/data -v /PATH/TO/BIDS/DIR:/data/bids -w /data neurobagel/bagelcli bids \
 --jsonld-path "DATASET.jsonld" --source-bids-dir "/PATH/TO/BIDS/DIR" --output "DATASET_BIDS.jsonld""
        echo "(For more information, see https://neurobagel.org/user_guide/cli/)"
        exit 1
    fi
fi

exec bagel "$@"
