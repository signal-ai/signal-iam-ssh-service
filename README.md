# signal-iam-ssh-service
A script that is executed by the sshd authorized_keys command to retreive active public ssh keys from IAM for a specific user for ssh login to AWS instances.

## Intention
We wanted a simple lightweight way of retrieving public keys with caching from IAM with no real granularity of role.

A user logs in to an aws instances with the standard ec2-user. The offered public key is given to the script to check if it exists in the cache. If it exists in cache then that specific public key is verified in IAM to see if it is active. This minimises IAM calls and also gives a real truth check for each public key. If the public key is accepted then the user can log in.

We log all of this including the users IAM user name to the systems secure syslog which can then be forwarded to any audit log one wishes.

## Use

Place the script on the system in `/path/to/iam-ssh.py`

Ensure the following lines are included in the sshd config:
```
AuthorizedKeysCommand /path/to/iam-ssh.py %k
AuthorizedKeysCommandUser nobody
```
The `%k` is the base64-encoded key or certificate for authentication. from [sshd](https://man.openbsd.org/sshd_config)

Ensure the script has the following permissions:

```
owner=root group=root mode=0755
```

Ensure the following variable is set correctly in the script for your systems syslog
```
SYSLOG_ADDRESS = '/dev/log'
```
