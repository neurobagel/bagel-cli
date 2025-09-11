#!/bin/bash

# This script assumes that you have set up a development Python environment and installed the bagel package following the instructions here:
# https://github.com/neurobagel/bagel-cli?tab=readme-ov-file#development-environment.
#
# Steps to use:
# 1. cd into the tests/neurobagel_examples submodule and create a new branch that will contain the updated example files
# 2. Navigate back to the bagel-cli repository root directory and run this script from there to regenerate the example synthetic JSONLD files inside of the tests/neurobagel_examples submodule
# in neurobagel_examples.
# 3. Navigate again to tests/neurobagel_examples and from there, commit the changes, push the changes to the submodule origin, and open a PR there to merge the updated examples.

data_dir=tests/neurobagel_examples/data-upload

# Phenotypic data only JSONLD
bagel pheno \
    --pheno "${data_dir}/example_synthetic.tsv" \
    --dictionary "${data_dir}/example_synthetic.json" \
    --name "BIDS synthetic" \
    --portal "https://github.com/bids-standard/bids-examples" \
    --output "${data_dir}/example_synthetic.jsonld" \
    --overwrite

# BIDS metadata table
# NOTE: Only regenerate if the table schema has changed (e.g., column names or format of columns changed, or new columns added).
# If the table schema hasn't changed, we don't want to regenerate this table since the local path to the BIDS files
# may be different each time (depending on the user running the script), and we want to avoid extraneous diffs in the path column.
# 
# bagel bids2tsv \
#     --bids-dir tests/bids-examples/synthetic \
#     --output "${data_dir}/example_synthetic_bids_metadata.tsv" \
#     --overwrite

# Phenotypic & BIDS data JSONLD
bagel bids \
    --jsonld-path ${data_dir}/example_synthetic.jsonld \
    --bids-table ${data_dir}/example_synthetic_bids_metadata.tsv \
    --dataset-source-dir /data/neurobagel/bagel-cli/bids-examples/synthetic \
    --output ${data_dir}/pheno-bids-output/example_synthetic_pheno-bids.jsonld \
    --overwrite

# Phenotypic & derivatives data JSONLD
bagel derivatives \
    --tabular ${data_dir}/nipoppy_proc_status_synthetic.tsv \
    --jsonld-path ${data_dir}/example_synthetic.jsonld \
    --output "${data_dir}/pheno-derivatives-output/example_synthetic_pheno-derivatives.jsonld" \
    --overwrite

# Phenotypic, BIDS, and derivatives data JSONLD
bagel derivatives \
    --tabular ${data_dir}/nipoppy_proc_status_synthetic.tsv \
    --jsonld-path "${data_dir}/pheno-bids-output/example_synthetic_pheno-bids.jsonld" \
    --output "${data_dir}/pheno-bids-derivatives-output/example_synthetic_pheno-bids-derivatives.jsonld" \
    --overwrite
