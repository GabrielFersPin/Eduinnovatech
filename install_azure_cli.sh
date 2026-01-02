`-#!/bin/bash
# Install Azure CLI on Ubuntu
# Reference: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-linux?pivots=apt

echo "🚀 Installing Azure CLI..."
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
echo "✅ Azure CLI installed. Verify with: az --version"
