# Use a Debian-based Python image for better ODBC driver compatibility
FROM python:3.9-slim-buster

# Install necessary packages for pyodbc and potential MDB Tools ODBC driver
# This part is CRITICAL for MS Access.
# The following assumes you're trying to use a Linux-compatible ODBC driver
# such as the MDBTools ODBC driver for .mdb files. For .accdb, native support
# on Linux is very limited without proprietary drivers or complex Wine setups.
# If this fails, consider migrating your Access DB to MySQL/PostgreSQL.
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc \
    unixodbc-dev \
    libmdbodbc1 \
    mdbtools \
    # Clean up apt caches to reduce image size
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Configure ODBC (Example, adjust for your driver)
# This tells unixODBC about the MDBTools driver.
# You might need to verify the path to libmdbodbc.so
RUN echo "[MDBTools ODBC Driver]\nDescription=MDBTools ODBC Driver\nDriver=/usr/lib/x86_64-linux-gnu/libmdbodbc.so\nSetup=/usr/lib/x86_64-linux-gnu/libmdbodbc.so\nFileUsage=1\n" >> /etc/odbcinst.ini
# Verify the driver name for pyodbc, it should match the name in odbcinst.ini
# In your Python code: DRIVER={MDBTools ODBC Driver} instead of {Microsoft Access Driver...}
# Test this carefully!

# Set working directory inside the container
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code and assets
COPY transcript_service.py .
COPY USP_logo.jpg .

# Expose the port Flask app runs on
EXPOSE 5000

# Command to run the Flask application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]