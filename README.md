## One-line installation on Ubuntu

After pushing this repository to GitHub, install the Community Edition on a fresh Ubuntu server with one command:

```bash
curl -fsSL https://raw.githubusercontent.com/OWNER/REPO/main/install.sh | sudo bash -s -- https://github.com/OWNER/REPO.git
```

The installer installs Docker when needed, creates production secrets, clones the repository into `/opt/nethealth-community`, builds the containers, and starts the web panel on port 80. Replace `OWNER/REPO` with your GitHub repository.

The web panel is included in Community. Community intentionally limits the scope to the free feature set: one MikroTik device, basic system/interface/ICMP/DHCP/routing monitoring, health and basic alerts, Telegram notification support, and `.rsc` configuration export. Advanced VPN, config diff, security audit, reports, capacity planning, automation, multi-tenant, and additional vendors remain Pro/Business scope.

# NetHealth Community

A small, on-premise, Dockerized MikroTik network monitoring platform.

## Community scope

- 1 MikroTik device
- Login/JWT
- MikroTik connection test
- Basic device inventory
- CPU / RAM / uptime
- Interface status + RX/TX + errors/drops when exposed by RouterOS
- WAN health using ICMP from the monitoring server
- DHCP pool usage when exposed by RouterOS
- Basic route and VPN visibility
- Health score
- Basic alerts
- Telegram notifications (optional)
- `.rsc` configuration export backup

The architecture is provider-based so Cisco/FortiGate/Huawei/SNMP can be added later.

## Quick start

1. Install Docker and Docker Compose plugin on Ubuntu.
2. Copy `.env.example` to `.env` and set values.
3. Run `docker compose up -d --build`.
4. Open `http://SERVER_IP`.
5. Create the first admin account.
6. On MikroTik, enable API-SSL or REST over HTTPS and create a restricted monitoring user.
7. Add the router in the web UI.

For RouterOS 7+, Community uses the RouterOS REST API at `/rest` over HTTPS (`www-ssl`). The RouterOS docs describe REST as a JSON wrapper around the console API and document the `/rest/export` command for configuration export.

## Security notes

- Put the monitoring server on the management VLAN.
- Restrict RouterOS management services to the monitoring server IP.
- Use a dedicated RouterOS account with the minimum permissions needed.
- Backups are sensitive. Store the `backups/` directory on encrypted storage and protect Docker volumes.
- Change all defaults before production.

## Development

Backend: FastAPI + SQLAlchemy + PostgreSQL + Redis.
Frontend: React + Vite.
Worker: Python polling process.

This is an MVP community edition, not a production-hardened enterprise release.
