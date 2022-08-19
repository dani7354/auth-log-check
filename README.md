# auth-log-check
This Python script reads through an auth.log file and matches the
lines against one or more regular expressions, which can be added at
the top of the file `check_logs.py`. The matches are parsed and inserted
as records in one or more CSV files and optionally sent in an e-mail to the
server admin. The overall purpose of the script is to monitor SSH connections
and login attempts. By changing the regular expressions and parsing functions
(`parsing.py`), it can be used for other log files as well.

## Usage
The script can be run from a terminal but is intended to be run as a cronjob:
```
$ ./check_logs.py -l "/var/log/auth.log" -o "/path/to/csv/files/" -ec "/path/to/email_config.json"
```

### Arguments explained:
* __-l or --logs__: Log files (required).
* __-o or --output-dir__: Path to directory for creating and updating the CSV files (required).
* __-ec or --email-config__: Path to email configuration file (optional).
See example in `auth_log_check/config/email_config_format.json`
