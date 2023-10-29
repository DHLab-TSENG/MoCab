# Use the condaforge/miniforge3 base image
FROM condaforge/miniforge3:latest

ENV PYTHONUNBUFFERED 1

# Set the working directory inside the Docker image
WORKDIR /app

# Copy the project files to the Docker image
COPY . /app

# Install project dependencies using Conda
RUN pip install -r requirement.txt

# Expose port if necessary (replace 8080 with your desired port)
EXPOSE 5050

# Specify the command to run your Python script(s)
CMD ["python", "__main__.py"]