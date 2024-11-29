#!/bin/sh

while true; do
  cp /data/taskmanager.rdb /backup/"$(data +%s)".rdb;
  sleep "$BACKUP_PERIOD";
done