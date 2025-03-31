FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        git \
        vim \
        curl \
        cmake \
        build-essential \
        libgstreamer1.0-dev \
        libgstreamer-plugins-base1.0-dev \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-rtsp \
        protobuf-compiler \
        python3-dev \
        python3-pip && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install --upgrade pip && \
    pip3 install \
        numpy==1.26.4 \
        fastapi==0.115.12 \
        uvicorn[standard]==0.34.0 \
        loguru==0.7.3

WORKDIR /workspace
RUN git clone --depth=1 -b 4.5.4 https://github.com/opencv/opencv && \
    cd opencv && \
    mkdir build && \
    cd build && \
    cmake \
        -D CMAKE_BUILD_TYPE=RELEASE \
        -D CMAKE_INSTALL_PREFIX=/usr/local \
        -D WITH_GSTREAMER=ON \
        -D WITH_CUDA=OFF \
        -D PYTHON3_EXECUTABLE=$(which python3) \
        -D PYTHON3_INCLUDE_DIR=$(python3 -c "from sysconfig import get_paths as gp; print(gp()['include'])") \
        -D PYTHON3_PACKAGES_PATH=$(python3 -c "from sysconfig import get_paths as gp; print(gp()['purelib'])") \
        -D PYTHON3_NUMPY_INCLUDE_DIRS=$(python3 -c "import numpy; print(numpy.get_include())") \
        .. && \
    make -j$(nproc) && \
    make install && \
    rm -rf /workspace/opencv

ENTRYPOINT ["bash", "-c"]