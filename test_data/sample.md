# System Administration

## Check disk usage
<!-- tags: system, disk, monitoring -->
```bash
df -h
```

## Find large files
<!-- tags: system, files, cleanup -->
```bash
find /home -type f -size +100M -exec ls -lh {} \; | awk '{ print $9 ": " $5 }'
```

# Docker Commands

## List running containers
<!-- tags: docker, containers, monitoring -->
```bash
docker ps
```

## Clean up unused Docker resources
<!-- tags: docker, cleanup, maintenance -->
```bash
docker system prune -a --volumes
```

## View container logs
<!-- tags: docker, logs, debugging -->
```bash
docker logs -f $CONTAINER_NAME
```

# Git Operations

## Interactive rebase
<!-- tags: git, rebase, history -->
```bash
git rebase -i HEAD~$NUMBER_OF_COMMITS
```

## Search commit history
<!-- tags: git, search, history -->
```bash
git log --grep="$SEARCH_TERM" --oneline
```

## Reset to remote
<!-- tags: git, reset, remote -->
```bash
git fetch origin && git reset --hard origin/$BRANCH_NAME
```

# Network Tools

## Port scan with nmap
<!-- tags: network, scanning, security -->
```bash
nmap -sS -O $TARGET_IP
```

## Check open ports
<!-- tags: network, ports, monitoring -->
```bash
netstat -tulpn | grep LISTEN
```