# Use the existing Miniforge base image
FROM condaforge/miniforge3:23.1.0-4 AS base
ENV TZ=Etc/GMT
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update &&\
    apt-get install -y --no-install-recommends build-essential software-properties-common &&\
    apt-get install -y pkg-config libhdf5-dev

# Install Python 3.9.16 in the base image
RUN conda install -c conda-forge python=3.9.16 && conda clean --all -f -y

# Create a new Conda environment named MoCab
RUN conda create -n MoCab python=3.9.16

# Set the shell to use Conda environment commands
SHELL ["conda", "run", "-n", "MoCab", "/bin/bash", "-c"]

# Install numpy and scikit-learn through conda in the MoCab environment
RUN conda install -n MoCab -c conda-forge numpy scikit-learn && conda clean --all -f -y

# Copy the requirements.txt to the container
COPY ./Backend/requirements.txt /tmp/requirements.txt

# Install other dependencies using pip within the MoCab environment
RUN pip --default-timeout=1200 install --no-cache-dir -r /tmp/requirements.txt

# Final stage
FROM condaforge/miniforge3:23.1.0-4 AS final

# Install Python in the final stage and set up the MoCab environment
RUN conda install -c conda-forge python=3.9.16 && conda clean --all -f -y
RUN conda create -n MoCab python=3.9.16

# Copy the MoCab environment from the base image
COPY --from=base /opt/conda/envs/MoCab /opt/conda/envs/MoCab

# Set the environment variable to use the installed environment
ENV PATH="/opt/conda/envs/MoCab/bin:$PATH"
ENV CONDA_DEFAULT_ENV=MoCab

# Initialize Conda environment activation
RUN echo "source activate MoCab" >> ~/.bashrc

# Preload libgomp to handle potential TLS issues
ENV LD_PRELOAD=/opt/conda/envs/MoCab/lib/python3.9/site-packages/scikit_learn.libs/libgomp-d22c30c5.so.1.0.0

# Set the working directory
WORKDIR /app

# Copy the application code
COPY ./Backend /app

EXPOSE 5000

# Activate environment before starting the application
CMD ["/bin/bash", "-c", "source activate MoCab && python __main__.py"]
