#!/usr/bin/env bash

# Copy runtime environment
env > /etc/environment

# Check if RUN_ONCE environment variable is set. In case, running the script now and exiting.
if [ "$RUN_ONCE" = "true" ]
then
    echo "RUN_ONCE environment variable is set. Running the script now and exiting."
    python main.py
    exit 0
fi

# Check if CRON_SCHEDULE environment variable is set
if [ -z "$CRON_SCHEDULE" ]
then
    echo "CRON_SCHEDULE environment variable is not set. Setting it to 4 AM everyday by default"
    CRON_SCHEDULE="0 4 * * *"
fi

# Setting up cron job
echo "$CRON_SCHEDULE root /usr/bin/env python3 /app/main.py >/proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab

# Run the cron
echo "Cron job is set to run at $CRON_SCHEDULE. Waiting for the cron to run..."
exec /usr/sbin/cron -f
