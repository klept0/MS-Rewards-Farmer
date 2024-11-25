#!/bin/bash

# Makes accounts.json

cat > /app/accounts.json <<EOF
[
    {
        "username": "${USERNAME}",
        "password": "${PASSWORD}",
        "proxy": "${PROXY:-}"
    }
]
EOF

# Makes config.yaml
cat > /app/config.yaml <<EOF
apprise:
  notify:
    incomplete-activity:
      enabled: True
      ignore-safeguard-info: True
    uncaught-exception:
      enabled: True
  summary: ALWAYS
default:
  geolocation: ${GEOLOCATION:-US} # Default a US is GEOLOCATION 
logging:
  level: INFO
retries:
  base_delay_in_seconds: 120
  max: 4
  strategy: EXPONENTIAL
EOF

echo "Files generated successfully."