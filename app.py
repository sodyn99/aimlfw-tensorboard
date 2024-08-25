from flask import Flask, request, render_template, redirect
import os
import subprocess
import logging
import threading
import time
import glob
import signal

# ANSI color codes
GREEN = '\033[92m'
RESET = '\033[0m'

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        if "TensorBoard started and accessible" in record.msg:
            record.msg = f"{GREEN}{record.msg}{RESET}"
        return super().format(record)

# Set up colored logging
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = Flask(__name__)
tensorboard_process = None

def run_command(command):
    """Helper function to run a shell command and log the output."""
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logger.error(f"Command failed with error: {result.stderr.decode()}")
        return False, result.stderr.decode()
    else:
        logger.info(f"Command output: {result.stdout.decode()}")
        return True, result.stdout.decode()

def stop_tensorboard():
    global tensorboard_process
    if tensorboard_process:
        logger.info("Stopping existing TensorBoard process")
        os.killpg(os.getpgid(tensorboard_process.pid), signal.SIGTERM)
        tensorboard_process.wait()
        tensorboard_process = None

def start_tensorboard():
    global tensorboard_process
    stop_tensorboard()  # Ensure any existing process is stopped
    os.environ['TENSORBOARD_HOSTNAME'] = 'localhost'
    tensorboard_process = subprocess.Popen(
        ["tensorboard", "--logdir", "/logs", "--host", "0.0.0.0", "--port", "6006"],
        env=os.environ,
        preexec_fn=os.setsid  # Create a new process group
    )
    time.sleep(5)  # Give TensorBoard some time to start
    logger.info("TensorBoard started and accessible at http://localhost:6006/")

def clean_log_directory(directory):
    """Remove all tfevents files in the given directory."""
    for file in glob.glob(os.path.join(directory, "events.out.tfevents.*")):
        try:
            os.remove(file)
            logger.info(f"Removed old tfevents file: {file}")
        except Exception as e:
            logger.error(f"Error removing file {file}: {str(e)}")

def process_model(trainingjob_name, version):
    directory = f"/logs/{trainingjob_name}/{version}/"
    os.makedirs(directory, exist_ok=True)

    # Download model
    download_command = f"curl -o {directory}model.zip http://tm.traininghost:32002/model/{trainingjob_name}/{version}/Model.zip"
    logger.info(f"Running command: {download_command}")
    success, output = run_command(download_command)
    if not success:
        return False, f"Error downloading model: {output}"

    # Unzip model
    unzip_command = f"unzip -j -o {directory}model.zip -d {directory}"
    logger.info(f"Running command: {unzip_command}")
    success, output = run_command(unzip_command)
    if not success:
        return False, f"Error unzipping model: {output}"

    # Clean up old tfevents files
    clean_log_directory("/logs")
    clean_log_directory(directory)

    # Convert model for TensorBoard
    convert_command = f"python3 /app/import_pb_to_tensorboard.py --model_dir {directory} --log_dir /logs"
    logger.info(f"Running command: {convert_command}")
    success, output = run_command(convert_command)
    if not success:
        return False, f"Error converting model for TensorBoard: {output}"

    # Remove zip file
    os.remove(f"{directory}model.zip")

    return True, None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        trainingjob_name = request.form['trainingjob_name']
        version = request.form['version']

        success, error_message = process_model(trainingjob_name, version)
        if not success:
            return render_template('index.html', error_message=error_message)

        start_tensorboard()  # Restart TensorBoard to reflect new data immediately

        tensorboard_url = f"http://localhost:6006/#graphs"
        logger.info(f"Redirecting to TensorBoard at {tensorboard_url}")
        return redirect(tensorboard_url)

    return render_template('index.html', error_message=None)

def periodic_cleanup():
    while True:
        clean_log_directory("/logs")
        time.sleep(3600)  # Run every hour

# Start periodic cleanup in a separate thread
threading.Thread(target=periodic_cleanup, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=32108)