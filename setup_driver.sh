#!/bin/bash

# Script to install Microsoft ODBC Driver 18 for SQL Server on Ubuntu 24.04
# Reference: https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server

echo "🚀 Starting ODBC Driver Installation..."

# 1. Ensure prerequisites are installed
if ! command -v curl &> /dev/null; then
    echo "Installing curl..."
    sudo apt-get update && sudo apt-get install -y curl
fi

# 2. Add Microsoft public key
echo "Adding Microsoft GPG key..."
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

# 3. Add Microsoft repository (forcing 24.04)
echo "Adding Microsoft repository..."
curl https://packages.microsoft.com/config/ubuntu/24.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

# 4. Install the driver
echo "Updating package lists..."
sudo apt-get update

echo "Installing msodbcsql18..."
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Optional: Install tools like sqlcmd and bcp
# sudo ACCEPT_EULA=Y apt-get install -y mssql-tools18

echo "✅ Installation Complete. You can now run the Python script."
