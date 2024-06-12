# Use a base image that includes ICU (e.g., Debian with ICU)
FROM debian:latest

# Install ICU package
RUN apt-get update && apt-get install -y libicu-dev

# Install Python, pip, and python3-venv
RUN apt-get install -y python3 python3-pip python3-venv

# Set the working directory in the container
WORKDIR /app

# Copy the application files into the container
COPY . .

# Create a virtual environment
RUN python3 -m venv venv

# Activate the virtual environment
RUN . venv/bin/activate

# Install Python dependencies within the virtual environment
RUN pip install -r requirements.txt

# Expose port 5000
EXPOSE 5000

# Command to run the Flask application
CMD ["python3", "app.py"]
