# syntax=docker/dockerfile:1
# Copyright 2026 Scion Frontiers & Antigravity
# Supreme Harness Container Image Build

ARG BASE_IMAGE
FROM ${BASE_IMAGE}

USER root

# 1. Install high-performance core developer & runtime utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    ripgrep \
    jq \
    curl \
    wget \
    nano \
    zsh \
    iptables \
    ipset \
    dnsutils \
    dbus-x11 \
    gnome-keyring \
    python3-pip \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Install git-delta for enhanced diff rendering (from Claude harness)
ARG GIT_DELTA_VERSION=0.18.2
RUN ARCH=$(dpkg --print-architecture) && \
    wget -q "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
    dpkg -i "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
    rm -f "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"

# 3. Setup user directories for supreme harness configuration and plugins
RUN mkdir -p /home/scion/.supreme \
             /home/scion/.supreme/plugins \
             /home/scion/.supreme/skills \
             /home/scion/.scion/harness \
  && chown -R scion:scion /home/scion/.supreme /home/scion/.scion

# 4. Copy firewall script with sudoer rule
COPY init-firewall.sh /usr/local/bin/init-firewall.sh
RUN chmod +x /usr/local/bin/init-firewall.sh && \
    echo "scion ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/scion-firewall && \
    chmod 0440 /etc/sudoers.d/scion-firewall

# 5. Copy wrapper and notify utilities
COPY apex-wrapper.sh /home/scion/.scion/harness/apex-wrapper.sh
COPY notify.sh /home/scion/.scion/harness/notify.sh
RUN chmod +x /home/scion/.scion/harness/apex-wrapper.sh \
             /home/scion/.scion/harness/notify.sh

# 6. Copy 16 built-in plugins
COPY plugins/ /home/scion/.supreme/plugins/
RUN chown -R scion:scion /home/scion/.supreme/plugins

ENV SHELL=/bin/zsh
ENV DEVCONTAINER=true

CMD ["/home/scion/.scion/harness/apex-wrapper.sh"]
