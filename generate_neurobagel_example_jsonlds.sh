#!/bin/bash
# Run from repository root

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
docker run --rm --volume=$PWD:/data/neurobagel/bagel-cli -w /data/neurobagel/bagel-cli bagel bids \
    --jsonld-path ${data_dir}/example_synthetic.jsonld \
    --bids-dir bids-examples/synthetic \
    --output ${data_dir}/pheno-bids-output/example_synthetic_pheno-bids.jsonld \
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
