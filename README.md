<div align="center">

# `bagel-cli`
[![Coverage Status](https://coveralls.io/repos/github/neurobagel/bagel-cli/badge.svg?branch=main)](https://coveralls.io/github/neurobagel/bagel-cli?branch=main)
[![Tests](https://github.com/neurobagel/bagel-cli/actions/workflows/test.yml/badge.svg)](https://github.com/neurobagel/bagel-cli/actions/workflows/test.yml)

</div>

The Bagel CLI is a simple Python command line tool to automatically read and annotate a 
[BIDS dataset](https://bids-specification.readthedocs.io/en/stable/) 
so that it can be integrated into the Neurobagel graph.

## Installation
### Docker
Option 1: Pull the Docker image for the CLI from DockerHub: `docker pull neurobagel/bagelcli`

Option 2: Clone the repository and build the Docker image locally:
```bash
git clone https://github.com/neurobagel/bagel-cli.git
cd bagel-cli
docker build -t bagel .
```

### Singularity
Build a Singularity image for `bagel-cli` using the DockerHub image:  
`singularity pull bagel.sif docker://neurobagel/bagelcli`

## Running the CLI
CLI commands can be accessed using the Docker/Singularity image you have built.

### To see the CLI options:
```bash
# Docker
docker run --rm bagel  # this is a shorthand for `docker run --rm bagel --help

# Singularity
singularity run bagel.sif
```
For a specific command:
```bash
# Docker
docker run --rm bagel <command-name> --help

# Singularity
singularity run bagel.sif <command-name> --help
```


### To run the CLI on data:
1. `cd` into your local directory containing (1) your phenotypic .tsv file, (2) Neurobagel-annotated data dictionary, and (3) BIDS directory (if available). 
2. Run a `bagel` container and include your CLI command at the end in the following format:
```bash
# Docker
docker run --rm --volume=$PWD:$PWD -w $PWD bagel <CLI command here>

# Singularity
singularity run --no-home --bind $PWD --pwd $PWD /path/to/bagel.sif <CLI command here>
```
In the above command, `--volume=$PWD:$PWD -w $PWD` (or `--bind $PWD --pwd $PWD` for Singularity) mounts your current working directory (containing all inputs for the CLI) at the same path inside the container, and also sets the _container's_ working directory to the mounted path (so it matches your location on your host machine). This allows you to pass paths to the containerized CLI which are composed the same way as on your local machine. (And both absolute paths and relative top-down paths from your working directory will work!)

### Example:  
If your data live in `/home/data/Dataset1`:
```
home/
└── data/
    └── Dataset1/
        ├── neurobagel/
        │   ├── Dataset1_pheno.tsv
        │   └── Dataset1_pheno.json
        └── bids/
            ├── sub-01
            ├── sub-02
            └── ...
```

You could run the following: (for a Singularity container, replace the first part of the Docker commands with the Singularity command from [the above template](#to-run-the-cli-on-data))
```bash
cd /home/data/Dataset1

# 1. Construct phenotypic subject dictionaries (pheno.jsonld)
docker run --rm --volume=$PWD:$PWD -w $PWD bagel pheno \
    --pheno "neurobagel/Dataset1_pheno.tsv" \
    --dictionary "neurobagel/Dataset1_pheno.json" \
    --output "neurobagel" \
    --name "Dataset1"

# 2. Add BIDS data to pheno.jsonld generated by step 1
docker run --rm --volume=$PWD:$PWD -w $PWD bagel bids \
    --jsonld-path "neurobagel/pheno.jsonld" \
    --bids-dir "bids" \
    --output "neurobagel"
```

## Update python lock-file

To ensure that our Docker images are built in a predictable way,
we use `requirements.txt` as a lock-file.
That is, `requirements.txt` includes the entire dependency tree of our tool,
with pinned versions for every dependency (see [also](https://pip.pypa.io/en/latest/topics/repeatable-installs/#repeatability))

The `requirements.txt` file is automatically generated from the `setup.cfg`
constraints. To update it, we use `pip-compile` from the `pip-tools` package.
Here is how you can use these tools to update the `requirements.txt` file.

To install:
```bash
pip install pip-tools
```

To run
```bash
pip-compile -o requirements.txt --upgrade
```

## Development environment

To set up a development environment, please run
```python
pip install -e '.[all]'
```

