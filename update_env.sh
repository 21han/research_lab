#!/bin/bash
set -e

conda env update --file env.yml
conda env export --no-build > env.yml
echo "env.yml file updated successfully";
