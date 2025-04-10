#!/bin/bash

# Steps to use:
# 1. cd into the tests/neurobagel_examples submodule and create a new branch that will contain the updated example files
# 2. Navigate back to the bagel-cli repository root directory and run this script from there to regenerate the example synthetic JSONLD files inside of the tests/neurobagel_examples submodule
# in neurobagel_examples.
# 3. Navigate again to tests/neurobagel_examples and from there, commit the changes, push the changes to the submodule origin, and open a PR there to merge the updated examples.

docker build -t bagel .
cd tests

data_dir=neurobagel_examples/data-upload

# Phenotypic data only JSONLD
docker run --rm --volume=$PWD:/data/neurobagel/bagel-cli -w /data/neurobagel/bagel-cli bagel pheno \
    --pheno "${data_dir}/example_synthetic.tsv" \
    --dictionary "${data_dir}/example_synthetic.json" \
    --name "BIDS synthetic" \
    --output "${data_dir}/example_synthetic.jsonld" \
    --overwrite

# Phenotypic & BIDS data JSONLD
docker run --rm --volume=$PWD/$data_dir:/data --volume=$PWD/bids-examples/synthetic:/data/bids -w /data bagel bids \
    --jsonld-path example_synthetic.jsonld \
    --bids-dir /data/neurobagel/bagel-cli/bids-examples/synthetic \
    --output pheno-bids-output/example_synthetic_pheno-bids.jsonld \
    --overwrite

# Phenotypic & derivatives data JSONLD
docker run --rm --volume=$PWD:/data/neurobagel/bagel-cli -w /data/neurobagel/bagel-cli bagel derivatives \
    --tabular ${data_dir}/nipoppy_proc_status_synthetic.tsv \
    --jsonld-path ${data_dir}/example_synthetic.jsonld \
    --output "${data_dir}/pheno-derivatives-output/example_synthetic_pheno-derivatives.jsonld" \
    --overwrite

# Phenotypic, BIDS, and derivatives data JSONLD
docker run --rm --volume=$PWD:/data/neurobagel/bagel-cli -w /data/neurobagel/bagel-cli bagel derivatives \
    --tabular ${data_dir}/nipoppy_proc_status_synthetic.tsv \
    --jsonld-path "${data_dir}/pheno-bids-output/example_synthetic_pheno-bids.jsonld" \
    --output "${data_dir}/pheno-bids-derivatives-output/example_synthetic_pheno-bids-derivatives.jsonld" \
    --overwrite
