# System Administration

## Check disk usage
```bash
df -h
```

## Find large files
```bash
find /home -type f -size +100M -exec ls -lh {} \; | awk '{ print $9 ": " $5 }'
```

# Docker Commands

## List running containers
```bash
docker ps
```

## Clean up unused Docker resources
```bash
docker system prune -a --volumes
```

## View container logs
```bash
docker logs -f container_name
```

# Git Operations

## Interactive rebase
```bash
git rebase -i HEAD~5
```

## Search commit history
```bash
git log --grep="search_term" --oneline
```

## Reset to remote
```bash
git fetch origin && git reset --hard origin/main
```

# Network Tools

## Port scan with nmap
```bash
nmap -sS -O 192.168.1.1
```

## Check open ports
```bash
netstat -tulpn | grep LISTEN
```

# Multi-Command Example

## Enumerate SMB shares
```bash
netexec smb $IP --shares
```

```
enum4linux-ng -A $IP
```
