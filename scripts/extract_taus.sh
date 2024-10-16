#!/bin/bash
find $1 -type f -name "python_agent.log" -exec bash -c '
  for file do
    echo "Processing file: $file"
    grep -oE "Tau: [0-9]+\.?[0-9]*" "$file" | awk "{print \$2}" > "$(dirname "$file")/taus.csv"
  done
' bash {} +
