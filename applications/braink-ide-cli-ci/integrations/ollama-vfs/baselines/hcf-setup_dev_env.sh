#!/bin/bash

# Keddeh Sovereign OS - Developer Environment Setup
# Installs Ollama (Local LLM) and Aider (AI Pair Programmer)

echo "=========================================================="
echo "🤖 Initializing Open-Source AI Developer Tools Setup..."
echo "=========================================================="

# 1. Environment Detection
OS="$(uname -s)"
ARCH="$(uname -m)"
echo "Detected Environment: $OS ($ARCH)"

# 2. Install Ollama
echo "----------------------------------------------------------"
echo "[1/3] Installing Ollama (Local Inference Engine)..."
if ! command -v ollama &> /dev/null; then
    if [ "$OS" = "Linux" ]; then
        curl -fsSL https://ollama.com/install.sh | sh
    elif [ "$OS" = "Darwin" ]; then
        echo "Please install Ollama from https://ollama.com/download/mac"
    else
        echo "Unsupported OS for automated Ollama installation. Please install manually."
    fi
else
    echo "✅ Ollama is already installed."
fi

# 3. Install Aider
echo "----------------------------------------------------------"
echo "[2/3] Installing Aider (AI Pair Programmer)..."
if ! command -v aider &> /dev/null; then
    if command -v python3 &> /dev/null; then
        echo "Installing aider-chat via pip..."
        python3 -m pip install --upgrade pip --quiet
        python3 -m pip install aider-chat --quiet
        echo "✅ Aider installed successfully."
    else
        echo "❌ Python3 is required to install aider. Please install python3 and try again."
        exit 1
    fi
else
    echo "✅ Aider is already installed."
fi

# 4. Configure Environment Paths
echo "----------------------------------------------------------"
echo "[3/3] Configuring Environment Paths & Aider config..."
USER_BIN_DIR="$HOME/.local/bin"
if [[ ":$PATH:" != *":$USER_BIN_DIR:"* ]]; then
    echo "Adding $USER_BIN_DIR to PATH (temporarily for this script)."
    export PATH="$HOME/.local/bin:$PATH"
    
    # Try to add to profile if possible
    if [ -f "$HOME/.bashrc" ]; then
        if ! grep -q "$USER_BIN_DIR" "$HOME/.bashrc"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            echo "Added $USER_BIN_DIR to PATH in ~/.bashrc"
        fi
    fi
fi

# 5. Create .aider.conf.yml
cat << 'AIDER_EOF' > .aider.conf.yml
# Aider Configuration for Local Workspace (Keddeh Sovereign)
# Defines local environment defaults and routing rules

model: ollama/qwen2.5-coder:7b
edit-format: diff
dark-mode: true
auto-commits: false
yes-always: false
stream: true
# Optional: point to local Ollama API base if customized
# openai-api-base: http://127.0.0.1:11434/v1
AIDER_EOF
echo "✅ Created standard .aider.conf.yml"

# 6. Distribute to Server Stacks
echo "----------------------------------------------------------"
echo "[4/4] Deploying setup environment to server stacks..."
STACKS_DIR="server_stacks"
if [ -d "$STACKS_DIR" ]; then
    cp .aider.conf.yml "$STACKS_DIR/"
    cp "$0" "$STACKS_DIR/setup_dev_env.sh"
    echo "✅ Deployed .aider.conf.yml and setup script to $STACKS_DIR"
    
    # If there are subdirectories inside server_stacks, deploy there too
    for d in "$STACKS_DIR"/*/; do
        if [ -d "$d" ]; then
            cp .aider.conf.yml "$d/"
            cp "$0" "$d/setup_dev_env.sh"
            echo "✅ Deployed to $d"
        fi
    done
fi

echo "=========================================================="
echo "🎉 Setup Complete!"
echo "To start coding with Aider using your local Ollama model:"
echo "1. Start ollama (if not running): ollama serve &"
echo "2. Pull the model: ollama pull qwen2.5-coder:7b"
echo "3. Run aider: aider"
echo "=========================================================="
