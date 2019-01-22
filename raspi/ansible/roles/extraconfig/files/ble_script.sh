#!/bin/bash
case "$1" in
	remove_ble_permissions)
		rm /tmp/ble_permissions.txt
		;;
	check_ble_signal)
		cat /tmp/ble_device_signals.csv
		;;
	add_ble_permissions)
		echo $2 > /tmp/ble_permissions.txt
		;;
	*)
		echo 'Permission Denied' 1>&2
		exit 1
		;;
esac
