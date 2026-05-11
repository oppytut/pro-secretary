#!/bin/bash

set -e

echo "================================================"
echo "AI Personal Secretary - Swap Space Setup"
echo "================================================"
echo ""

SWAP_SIZE=${1:-8G}

echo "Creating ${SWAP_SIZE} swap file..."
echo ""

if [ -f /swapfile ]; then
    echo "⚠️  Swap file already exists at /swapfile"
    echo "Current swap status:"
    swapon --show
    echo ""
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    
    echo "Disabling existing swap..."
    sudo swapoff /swapfile
    sudo rm /swapfile
fi

echo "Step 1/6: Creating swap file (${SWAP_SIZE})..."
sudo fallocate -l ${SWAP_SIZE} /swapfile

echo "Step 2/6: Setting permissions..."
sudo chmod 600 /swapfile

echo "Step 3/6: Setting up swap area..."
sudo mkswap /swapfile

echo "Step 4/6: Enabling swap..."
sudo swapon /swapfile

echo "Step 5/6: Making swap permanent..."
if ! grep -q '/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✓ Added to /etc/fstab"
else
    echo "✓ Already in /etc/fstab"
fi

echo "Step 6/6: Optimizing swap settings..."
sudo sysctl vm.swappiness=10
sudo sysctl vm.vfs_cache_pressure=50

if ! grep -q 'vm.swappiness' /etc/sysctl.conf; then
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
    echo "✓ Swap settings saved to /etc/sysctl.conf"
else
    echo "✓ Swap settings already in /etc/sysctl.conf"
fi

echo ""
echo "================================================"
echo "✅ Swap setup complete!"
echo "================================================"
echo ""
echo "Current memory status:"
free -h
echo ""
echo "Swap details:"
swapon --show
echo ""
echo "Swap is now active and will persist across reboots."
echo ""
