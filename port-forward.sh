#!/bin/bash

# Function to start port forwarding with retry
start_port_forward() {
    local command=$1
    local max_retries=5
    local retry_interval=5

    while true; do
        $command &
        local pid=$!
        echo "Started port forwarding: $command (PID: $pid)"

        # Wait for the process to finish
        wait $pid

        # Check if the process exited unexpectedly
        if [ $? -ne 0 ]; then
            echo "Port forwarding failed: $command"
            local retries=0
            while [ $retries -lt $max_retries ]; do
                echo "Retrying in $retry_interval seconds... (Attempt $((retries+1))/$max_retries)"
                sleep $retry_interval
                $command &
                pid=$!
                echo "Restarted port forwarding: $command (PID: $pid)"
                wait $pid
                if [ $? -eq 0 ]; then
                    break
                fi
                retries=$((retries+1))
            done
            if [ $retries -eq $max_retries ]; then
                echo "Max retries reached for: $command"
            fi
        fi
    done
}

# Start port forwarding for the specified services
start_port_forward "kubectl port-forward svc/my-release-influxdb 8086:8086" &
start_port_forward "kubectl port-forward svc/flask-service 32108:32108 -n traininghost" &
start_port_forward "kubectl port-forward svc/tensorboard-service 6006:6006 -n traininghost" &

# Keep the script running
echo "Port forwarding is active. Press Ctrl+C to stop all port-forwarding processes."
trap "kill 0" SIGINT
wait