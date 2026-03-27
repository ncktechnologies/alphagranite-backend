#!/bin/bash

set -euo pipefail

./deploy-stack.sh dev
./deploy-stack.sh staging
