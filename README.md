# redis-ha-demo

A project for demostrating a redis master-slave cluster with sentinels.

## Topology

Masters are called M1, M2, M3, ..., Mn.
Slaves are called R1, R2, R3, ..., Rn (R stands for replica).
Sentinels are called S1, S2, S3, ..., Sn.
Clients are called C1, C2, C3, ..., Cn.

    +----+    +----+    +----+
    | M1 |----| R1 |----| R2 |
    +----+    +----+    +----+
                 |
    +------------+------------+
    |            |            |
    |            |            |
    +----+       +----+       +----+
    | S1 |       | S2 |       | S3 |
    +----+       +----+       +----+
    |            |
    |            |
    +----+       +----+
    | C1 |       | C2 |
    +----+       +----+

    Configuration: quorum = 2

## Verification Steps

### General Setups
Using following command to start redis cluster. Meanwhile, a monitoring tool (redmon) and a demo application (a python app) should be started either.

```bash
docker-compose up
```

From the log, you can see there is one master and two slaves. Meanwhile, the client is writing and reading a key (timestamp).
```bash
demoapp      | [2019-07-26 02:34:23.525][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 02:34:23.526][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379), ('172.23.0.4', 6379)]
demoapp      | [2019-07-26 02:34:23.530][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 02:34:23'
```

### Sentinels

Using following command to pause a redis-sentinel-1.

```bash
docker pause redis-sentinel-1
```

From the log, you will get following log entries that indicates redis-sentinel-1 is down. But the whole cluster is still working properly.
```bash
demoapp      | [2019-07-26 02:39:54.992][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 02:39:54'
redis-sentinel-2 | 1:X 26 Jul 02:39:55.598 # +sdown sentinel 9a8f27c0b49b38cdd4df0e6b1a8698ec4e5dfc63 172.23.0.6 26379 @ mymaster 172.23.0.3 6379
redis-sentinel-3 | 1:X 26 Jul 02:39:56.007 # +sdown sentinel 9a8f27c0b49b38cdd4df0e6b1a8698ec4e5dfc63 172.23.0.6 26379 @ mymaster 172.23.0.3 6379
demoapp      | [2019-07-26 02:39:56.097][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 02:39:56.098][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.5', 6379)]
demoapp      | [2019-07-26 02:39:56.103][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 02:39:56'
```

Keep on pausing redis-sentinel-2
```bash
docker pause redis-sentinel-2
```

From the log, you will get following log entries that indicates redis-sentinel-2 is down. But the whole cluster is still working properly.
```bash
redis-sentinel-3 | 1:X 26 Jul 02:42:31.888 # +sdown sentinel 5389774d80d4ae4b85b1b1a92bc56660d1bbe89d 172.23.0.7 26379 @ mymaster 172.23.0.3 6379
demoapp      | [2019-07-26 02:42:32.167][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 02:42:32.168][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.5', 6379)]
demoapp      | [2019-07-26 02:42:32.172][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 02:42:32'
```

Keep on pausing redis-sentinel-3
```bash
docker pause redis-sentinel-3
```

From the log, you will get following log entries that indicates the cluster is unhealthy.
```bash
demoapp      | [2019-07-26 02:43:37.718][app.py:39][ERROR]No master found for 'mymaster'
demoapp      | [2019-07-26 02:43:39.023][app.py:39][ERROR]No master found for 'mymaster'
demoapp      | [2019-07-26 02:43:40.328][app.py:39][ERROR]No master found for 'mymaster'
demoapp      | [2019-07-26 02:43:41.634][app.py:39][ERROR]No master found for 'mymaster'
demoapp      | [2019-07-26 02:43:42.940][app.py:39][ERROR]No master found for 'mymaster'
demoapp      | [2019-07-26 02:43:44.246][app.py:39][ERROR]No master found for 'mymaster'
demoapp      | [2019-07-26 02:43:45.552][app.py:39][ERROR]No master found for 'mymaster'
demoapp      | [2019-07-26 02:43:46.857][app.py:39][ERROR]No master found for 'mymaster'
demoapp      | [2019-07-26 02:43:48.163][app.py:39][ERROR]No master found for 'mymaster'
```

It's reasonable to get these errors because the client relies on sentinel to discover master and slave nodes.
```py
sentinel = Sentinel(sentinels, socket_timeout=0.1)
logger.debug('Cluster Master: %s', str(sentinel.discover_master('mymaster')))
logger.debug('Cluster Slave: %s', str(sentinel.discover_slaves('mymaster')))

master = sentinel.master_for('mymaster', socket_timeout=0.1, password='<password>')
slave = sentinel.slave_for('mymaster', socket_timeout=0.1, password='<password>')
```

Using following command to unpause sentinels.
```bash
docker unpause redis-sentinel-1
docker unpause redis-sentinel-2
docker unpause redis-sentinel-3
```

You will see the restore messages (+titl, -tilt, -sdown) from sentinels.
```bash
demoapp      | [2019-07-26 02:49:05.653][app.py:39][ERROR]No master found for 'mymaster'
redis-sentinel-1 | 1:X 26 Jul 02:49:06.681 # +tilt #tilt mode entered
demoapp      | [2019-07-26 02:49:06.960][app.py:39][ERROR]No master found for 'mymaster'
redis-sentinel-2 | 1:X 26 Jul 02:49:07.018 # +tilt #tilt mode entered
demoapp      | [2019-07-26 02:49:07.963][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 02:49:07.964][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379), ('172.23.0.4', 6379)]
demoapp      | [2019-07-26 02:49:07.968][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 02:49:07'
redis-sentinel-3 | 1:X 26 Jul 02:49:08.343 # +tilt #tilt mode entered
demoapp      | [2019-07-26 02:49:36.207][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 02:49:36.208][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379), ('172.23.0.4', 6379)]
demoapp      | [2019-07-26 02:49:36.212][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 02:49:36'
redis-sentinel-1 | 1:X 26 Jul 02:49:36.727 # -tilt #tilt mode exited
redis-sentinel-2 | 1:X 26 Jul 02:49:37.075 # -tilt #tilt mode exited
redis-sentinel-2 | 1:X 26 Jul 02:49:37.075 # -sdown sentinel 9a8f27c0b49b38cdd4df0e6b1a8698ec4e5dfc63 172.23.0.6 26379 @ mymaster 172.23.0.3 6379
demoapp      | [2019-07-26 02:49:37.214][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 02:49:37.215][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379), ('172.23.0.4', 6379)]
demoapp      | [2019-07-26 02:49:37.219][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 02:49:37'
demoapp      | [2019-07-26 02:49:38.221][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 02:49:38.222][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379), ('172.23.0.4', 6379)]
demoapp      | [2019-07-26 02:49:38.226][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 02:49:38'
redis-sentinel-3 | 1:X 26 Jul 02:49:38.370 # -tilt #tilt mode exited
redis-sentinel-3 | 1:X 26 Jul 02:49:38.370 # -sdown sentinel 9a8f27c0b49b38cdd4df0e6b1a8698ec4e5dfc63 172.23.0.6 26379 @ mymaster 172.23.0.3 6379
redis-sentinel-3 | 1:X 26 Jul 02:49:38.370 # -sdown sentinel 5389774d80d4ae4b85b1b1a92bc56660d1bbe89d 172.23.0.7 26379 @ mymaster 172.23.0.3 6379
demoapp      | [2019-07-26 02:49:39.229][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 02:49:39.230][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379), ('172.23.0.4', 6379)]
demoapp      | [2019-07-26 02:49:39.234][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 02:49:39'
```

### Slaves

Before doing following steps, please make sure that you have a healthy cluster.

Using following command to pause redis-slave-1.
```bash
docker pause redis-slave-1
```

After running the command, messages from sentinels indicate that redis-slave-1 is down. Meanwhile, the client only get a slave from sentinel.
```bash
redis-sentinel-3 | 1:X 26 Jul 03:02:47.923 # +sdown slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.3 6379
redis-sentinel-2 | 1:X 26 Jul 03:02:47.998 # +sdown slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 03:02:48.342 # +sdown slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.3 6379
demoapp      | [2019-07-26 03:02:48.461][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:02:48.464][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379)]
demoapp      | [2019-07-26 03:02:48.475][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 03:02:48'
demoapp      | [2019-07-26 03:02:49.478][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:02:49.479][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379)]
```

Keep on pausing redis-slave-2.
```bash
docker pause redis-slave-2
```

After running the command, messages from sentinels indicate that redis-slave-2 is down. Meanwhile, the client only get a empty slave list from sentinel. This cluster is not high-avalibility cluster any more.
```bash
demoapp      | [2019-07-26 03:07:05.712][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 03:07:05'
demoapp      | [2019-07-26 03:07:06.715][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:07:06.718][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379)]
demoapp      | [2019-07-26 03:07:06.825][app.py:39][ERROR]Timeout reading from socket
demoapp      | [2019-07-26 03:07:07.828][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:07:07.829][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379)]
demoapp      | [2019-07-26 03:07:07.932][app.py:39][ERROR]Timeout reading from socket
demoapp      | [2019-07-26 03:07:08.935][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:07:08.936][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379)]
demoapp      | [2019-07-26 03:07:09.039][app.py:39][ERROR]Timeout reading from socket
demoapp      | [2019-07-26 03:07:10.041][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:07:10.042][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379)]
demoapp      | [2019-07-26 03:07:10.146][app.py:39][ERROR]Timeout reading from socket
demoapp      | [2019-07-26 03:07:11.149][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:07:11.150][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379)]
demoapp      | [2019-07-26 03:07:11.253][app.py:39][ERROR]Timeout reading from socket
redis-sentinel-1 | 1:X 26 Jul 03:07:12.145 # +sdown slave 172.23.0.5:6379 172.23.0.5 6379 @ mymaster 172.23.0.3 6379
demoapp      | [2019-07-26 03:07:12.256][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:07:12.258][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379)]
redis-sentinel-2 | 1:X 26 Jul 03:07:12.271 # +sdown slave 172.23.0.5:6379 172.23.0.5 6379 @ mymaster 172.23.0.3 6379
demoapp      | [2019-07-26 03:07:12.362][app.py:39][ERROR]Timeout reading from socket
redis-sentinel-3 | 1:X 26 Jul 03:07:12.397 # +sdown slave 172.23.0.5:6379 172.23.0.5 6379 @ mymaster 172.23.0.3 6379
demoapp      | [2019-07-26 03:07:13.365][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:07:13.370][app.py:31][DEBUG]Cluster Slave: []
demoapp      | [2019-07-26 03:07:13.375][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 03:07:13'
demoapp      | [2019-07-26 03:07:14.379][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:07:14.384][app.py:31][DEBUG]Cluster Slave: []
```

Using following command to unpause slaves.
```bash
docker unpause redis-slave-1
docker unpause redis-slave-2
```

After unpausing the slaves, please pay attention to the restore messages between master and slave.

```bash
demoapp      | [2019-07-26 03:10:33.450][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 03:10:33'
demoapp      | [2019-07-26 03:10:34.453][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:10:34.460][app.py:31][DEBUG]Cluster Slave: []
demoapp      | [2019-07-26 03:10:34.473][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 03:10:34'
redis-slave-1 | 1:S 26 Jul 03:10:34.718 # Connection with master lost.
redis-slave-1 | 1:S 26 Jul 03:10:34.718 * Caching the disconnected master state.
redis-sentinel-1 | 1:X 26 Jul 03:10:34.761 # -sdown slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.3 6379
redis-sentinel-2 | 1:X 26 Jul 03:10:34.770 # -sdown slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.3 6379
redis-sentinel-3 | 1:X 26 Jul 03:10:34.808 # -sdown slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.3 6379
redis-slave-1 | 1:S 26 Jul 03:10:35.011 * Connecting to MASTER 172.23.0.3:6379
redis-slave-1 | 1:S 26 Jul 03:10:35.012 * MASTER <-> SLAVE sync started
redis-slave-1 | 1:S 26 Jul 03:10:35.012 * Non blocking connect for SYNC fired the event.
redis-slave-1 | 1:S 26 Jul 03:10:35.012 * Master replied to PING, replication can continue...
redis-slave-1 | 1:S 26 Jul 03:10:35.013 * Trying a partial resynchronization (request a524c2ea051d23420c54fca9b8c614b7a768d11c:1005812).
redis-slave-1 | 1:S 26 Jul 03:10:35.013 * Successful partial resynchronization with master.
redis-slave-1 | 1:S 26 Jul 03:10:35.013 * MASTER <-> SLAVE sync: Master accepted a Partial Resynchronization.
redis-master | 1:M 26 Jul 03:10:35.013 * Slave 172.23.0.4:6379 asks for synchronization
redis-master | 1:M 26 Jul 03:10:35.013 * Partial resynchronization request from 172.23.0.4:6379 accepted. Sending 236003 bytes of backlog starting from offset 1005812.
demoapp      | [2019-07-26 03:10:35.477][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:10:35.478][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379)]
demoapp      | [2019-07-26 03:10:35.483][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 03:10:35'
redis-sentinel-1 | 1:X 26 Jul 03:10:35.860 # -sdown slave 172.23.0.5:6379 172.23.0.5 6379 @ mymaster 172.23.0.3 6379
redis-sentinel-2 | 1:X 26 Jul 03:10:35.862 # -sdown slave 172.23.0.5:6379 172.23.0.5 6379 @ mymaster 172.23.0.3 6379
redis-slave-2 | 1:S 26 Jul 03:10:35.870 # Connection with master lost.
redis-slave-2 | 1:S 26 Jul 03:10:35.870 * Caching the disconnected master state.
redis-sentinel-3 | 1:X 26 Jul 03:10:35.907 # -sdown slave 172.23.0.5:6379 172.23.0.5 6379 @ mymaster 172.23.0.3 6379
redis-slave-2 | 1:S 26 Jul 03:10:36.357 * Connecting to MASTER 172.23.0.3:6379
redis-slave-2 | 1:S 26 Jul 03:10:36.357 * MASTER <-> SLAVE sync started
redis-slave-2 | 1:S 26 Jul 03:10:36.357 * Non blocking connect for SYNC fired the event.
redis-slave-2 | 1:S 26 Jul 03:10:36.358 * Master replied to PING, replication can continue...
redis-slave-2 | 1:S 26 Jul 03:10:36.358 * Trying a partial resynchronization (request a524c2ea051d23420c54fca9b8c614b7a768d11c:1156925).
redis-master | 1:M 26 Jul 03:10:36.358 * Slave 172.23.0.5:6379 asks for synchronization
redis-master | 1:M 26 Jul 03:10:36.359 * Partial resynchronization request from 172.23.0.5:6379 accepted. Sending 85349 bytes of backlog starting from offset 1156925.
redis-slave-2 | 1:S 26 Jul 03:10:36.359 * Successful partial resynchronization with master.
redis-slave-2 | 1:S 26 Jul 03:10:36.359 * MASTER <-> SLAVE sync: Master accepted a Partial Resynchronization.
demoapp      | [2019-07-26 03:10:36.486][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 03:10:36.487][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379), ('172.23.0.4', 6379)]
```

### Master

## References
https://redis.io/topics/sentinel
https://medium.com/@amila922/redis-sentinel-high-availability-everything-you-need-to-know-from-dev-to-prod-complete-guide-deb198e70ea6
