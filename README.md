# `bagel-cli`

The Bagel CLI is a simple Python command line tool to automatically read and annotate a 
[BIDS dataset](https://bids-specification.readthedocs.io/en/stable/) 
so that it can be integrated into the Neurobagel graph.

## Installation
### Docker
To run the CLI in a Docker container:
1. [Install Docker](https://docs.docker.com/get-docker/).
2. Clone the repository and build the Docker image locally:
```bash
git clone https://github.com/neurobagel/bagel-cli.git
cd bagel-cli
docker build -t bagel .
```
3. `cd` into your local directory containing your phenotypic .tsv file, Neurobagel-annotated data dictionary, and BIDS directory (if present). Run a `bagel` container with the working directory mounted into the container (and set it as the working directory inside the container), and include your CLI command at the end in the following format:
```bash
docker run --rm --volume=/$PWD:$PWD -w $PWD bagel <CLI command here>
```
For example:
```bash
# 1. Construct phenotypic subject dictionaries (pheno.jsonld)
docker run --rm --volume=/$PWD:$PWD -w $PWD bagel pheno --pheno "path/to/tsv" --dictionary "path/to/annotated/json" --output "path/to/save/output" --name "dataset name"

# 2. Add BIDS data to pheno.jsonld
docker run --rm --volume=/$PWD:$PWD -w $PWD bagel bids --jsonld-path "path/to/pheno.jsonld/from/step1" --bids-dir "path/to/bids/directory" --output "path/to/save/output"
```

## Development environment

To set up a development environment, please run
```python
pip install -e '.[all]'
```