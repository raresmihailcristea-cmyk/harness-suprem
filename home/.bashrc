# Seed .bashrc for Supreme Harness
if [ -f "/home/scion/.scion/env" ]; then
    source "/home/scion/.scion/env"
fi

export PATH="/home/scion/.local/bin:/usr/local/bin:$PATH"
export NO_COLOR=1
export DEVCONTAINER=true
