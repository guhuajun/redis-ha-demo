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

## Initial configurations

### Master and slave nodes

Master and slave nodes are started with following parameters.

```bash
redis-server --requirepass 123456 --masterauth 123456
redis-server --slaveof redis-master 6379 --requirepass 123456 --masterauth 123456
```

### Sentinel

Sentinels are started with following initial configurations.
**Note: Configurations will be changed when master node failover is triggered.**

```conf
port 26379
dir "/tmp"
sentinel myid 9a8f27c0b49b38cdd4df0e6b1a8698ec4e5dfc63
sentinel monitor mymaster 172.23.0.3 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 5000
sentinel auth-pass mymaster 123456
```

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

From the log, you will get following log entries that indicate redis-sentinel-1 is down. But the whole cluster is still working properly.
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

From the log, you will get following log entries that indicate redis-sentinel-2 is down. But the whole cluster is still working properly.
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

From the log, you will get following log entries that indicate the cluster is unhealthy.
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

**Note: Before executing following steps, please make sure that you have a healthy cluster.**

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

**Note: Before executing following steps, please make sure that you have a healthy cluster.**

Using following command to pause redis-master.
```bash
docker pause redis-master
```

After pausing the master node, a failover will be triggered.
```bash
demoapp      | [2019-07-26 06:40:35.432][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 06:40:35.433][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379), ('172.23.0.4', 6379)]
demoapp      | [2019-07-26 06:40:35.437][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:40:35'
redis-sentinel-1 | 1:X 26 Jul 2019 06:40:35.526 * +fix-slave-config slave 172.23.0.5:6379 172.23.0.5 6379 @ mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:40:35.526 * +fix-slave-config slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.3 6379
redis-slave-1 | 1:S 26 Jul 2019 06:40:35.527 # Connection with master lost.
redis-master | 1:M 26 Jul 2019 06:40:35.527 # Connection with replica 172.23.0.5:6379 lost.
redis-master | 1:M 26 Jul 2019 06:40:35.527 # Connection with replica 172.23.0.4:6379 lost.
redis-slave-1 | 1:S 26 Jul 2019 06:40:35.527 * Caching the disconnected master state.
redis-slave-1 | 1:S 26 Jul 2019 06:40:35.527 * REPLICAOF 172.23.0.3:6379 enabled (user request from 'id=4 addr=172.23.0.6:60264 fd=9 name=sentinel-9a8f27c0-cmd age=10 idle=0 flags=x db=0 sub=0 psub=0 multi=3 qbuf=150 qbuf-free=32618 obl=36 oll=0 omem=0 events=r cmd=exec')
redis-slave-2 | 1:S 26 Jul 2019 06:40:35.526 # Connection with master lost.
redis-slave-2 | 1:S 26 Jul 2019 06:40:35.526 * Caching the disconnected master state.
redis-slave-2 | 1:S 26 Jul 2019 06:40:35.527 * REPLICAOF 172.23.0.3:6379 enabled (user request from 'id=4 addr=172.23.0.6:40210 fd=9 name=sentinel-9a8f27c0-cmd age=10 idle=0 flags=x db=0 sub=0 psub=0 multi=3 qbuf=150 qbuf-free=32618 obl=36 oll=0 omem=0 events=r cmd=exec')
redis-slave-2 | 1:S 26 Jul 2019 06:40:35.827 * Connecting to MASTER 172.23.0.3:6379
redis-slave-2 | 1:S 26 Jul 2019 06:40:35.827 * MASTER <-> REPLICA sync started
redis-slave-2 | 1:S 26 Jul 2019 06:40:35.827 * Non blocking connect for SYNC fired the event.
redis-slave-2 | 1:S 26 Jul 2019 06:40:35.827 * Master replied to PING, replication can continue...
redis-slave-2 | 1:S 26 Jul 2019 06:40:35.827 * Trying a partial resynchronization (request c465dda6926dad2c57e23289b0cec185a83c7d81:5604).
redis-slave-2 | 1:S 26 Jul 2019 06:40:35.828 * Successful partial resynchronization with master.
redis-slave-2 | 1:S 26 Jul 2019 06:40:35.828 * MASTER <-> REPLICA sync: Master accepted a Partial Resynchronization.
redis-master | 1:M 26 Jul 2019 06:40:35.828 * Replica 172.23.0.5:6379 asks for synchronization
redis-master | 1:M 26 Jul 2019 06:40:35.828 * Partial resynchronization request from 172.23.0.5:6379 accepted. Sending 135 bytes of backlog starting from offset 5604.
redis-slave-1 | 1:S 26 Jul 2019 06:40:35.833 * Connecting to MASTER 172.23.0.3:6379
redis-slave-1 | 1:S 26 Jul 2019 06:40:35.833 * MASTER <-> REPLICA sync started
redis-slave-1 | 1:S 26 Jul 2019 06:40:35.833 * Non blocking connect for SYNC fired the event.
redis-slave-1 | 1:S 26 Jul 2019 06:40:35.834 * Master replied to PING, replication can continue...
redis-master | 1:M 26 Jul 2019 06:40:35.834 * Replica 172.23.0.4:6379 asks for synchronization
redis-master | 1:M 26 Jul 2019 06:40:35.834 * Partial resynchronization request from 172.23.0.4:6379 accepted. Sending 135 bytes of backlog starting from offset 5604.
redis-slave-1 | 1:S 26 Jul 2019 06:40:35.834 * Trying a partial resynchronization (request c465dda6926dad2c57e23289b0cec185a83c7d81:5604).
redis-slave-1 | 1:S 26 Jul 2019 06:40:35.834 * Successful partial resynchronization with master.
redis-slave-1 | 1:S 26 Jul 2019 06:40:35.834 * MASTER <-> REPLICA sync: Master accepted a Partial Resynchronization.
demoapp      | [2019-07-26 06:40:36.439][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 06:40:36.441][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379), ('172.23.0.4', 6379)]
demoapp      | [2019-07-26 06:40:36.446][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:40:36'
demoapp      | [2019-07-26 06:41:08.007][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 06:41:08.008][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379), ('172.23.0.4', 6379)]
demoapp      | [2019-07-26 06:41:08.111][app.py:39][ERROR]Timeout reading from socket
demoapp      | [2019-07-26 06:41:09.116][app.py:30][DEBUG]Cluster Master: ('172.23.0.3', 6379)
demoapp      | [2019-07-26 06:41:09.117][app.py:31][DEBUG]Cluster Slave: [('172.23.0.5', 6379), ('172.23.0.4', 6379)]
demoapp      | [2019-07-26 06:41:09.219][app.py:39][ERROR]Timeout reading from socket
redis-sentinel-2 | 1:X 26 Jul 2019 06:41:09.591 # +sdown master mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:10.020 # +sdown master mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:10.104 # +odown master mymaster 172.23.0.3 6379 #quorum 2/2
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:10.104 # +new-epoch 1
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:10.104 # +try-failover master mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:10.113 # +vote-for-leader 9a8f27c0b49b38cdd4df0e6b1a8698ec4e5dfc63 1
redis-sentinel-3 | 1:X 26 Jul 2019 06:41:10.116 # +new-epoch 1
redis-sentinel-2 | 1:X 26 Jul 2019 06:41:10.118 # +new-epoch 1
redis-sentinel-3 | 1:X 26 Jul 2019 06:41:10.120 # +vote-for-leader 9a8f27c0b49b38cdd4df0e6b1a8698ec4e5dfc63 1
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:10.121 # 120978a92740fcdef29b0361df53a3aff0f0824b voted for 9a8f27c0b49b38cdd4df0e6b1a8698ec4e5dfc63 1
redis-sentinel-2 | 1:X 26 Jul 2019 06:41:10.122 # +vote-for-leader 9a8f27c0b49b38cdd4df0e6b1a8698ec4e5dfc63 1
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:10.122 # 5389774d80d4ae4b85b1b1a92bc56660d1bbe89d voted for 9a8f27c0b49b38cdd4df0e6b1a8698ec4e5dfc63 1
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:10.167 # +elected-leader master mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:10.167 # +failover-state-select-slave master mymaster 172.23.0.3 6379
redis-sentinel-3 | 1:X 26 Jul 2019 06:41:10.191 # +sdown master mymaster 172.23.0.3 6379
demoapp      | [2019-07-26 06:41:10.227][app.py:39][ERROR]No master found for 'mymaster'
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:10.250 # +selected-slave slave 172.23.0.5:6379 172.23.0.5 6379 @ mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:10.251 * +failover-state-send-slaveof-noone slave 172.23.0.5:6379 172.23.0.5 6379 @ mymaster 172.23.0.3 6379
redis-sentinel-3 | 1:X 26 Jul 2019 06:41:10.268 # +odown master mymaster 172.23.0.3 6379 #quorum 3/2
redis-sentinel-3 | 1:X 26 Jul 2019 06:41:10.268 # Next failover delay: I will not start a failover before Fri Jul 26 06:41:20 2019
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:10.327 * +failover-state-wait-promotion slave 172.23.0.5:6379 172.23.0.5 6379 @ mymaster 172.23.0.3 6379
redis-slave-2 | 1:M 26 Jul 2019 06:41:10.328 # Setting secondary replication ID to c465dda6926dad2c57e23289b0cec185a83c7d81, valid up to offset: 24375. New replication ID is 3dba1fcea0cab761dc959243ea26399cc93811fd
redis-slave-2 | 1:M 26 Jul 2019 06:41:10.328 # Connection with master lost.
redis-slave-2 | 1:M 26 Jul 2019 06:41:10.328 * Caching the disconnected master state.
redis-slave-2 | 1:M 26 Jul 2019 06:41:10.328 * Discarding previously cached master state.
redis-slave-2 | 1:M 26 Jul 2019 06:41:10.328 * MASTER MODE enabled (user request from 'id=4 addr=172.23.0.6:40210 fd=9 name=sentinel-9a8f27c0-cmd age=45 idle=0 flags=x db=0 sub=0 psub=0 multi=3 qbuf=140 qbuf-free=32628 obl=36 oll=0 omem=0 events=r cmd=exec')
redis-sentinel-2 | 1:X 26 Jul 2019 06:41:10.720 # +odown master mymaster 172.23.0.3 6379 #quorum 3/2
redis-sentinel-2 | 1:X 26 Jul 2019 06:41:10.720 # Next failover delay: I will not start a failover before Fri Jul 26 06:41:20 2019
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:11.136 # +promoted-slave slave 172.23.0.5:6379 172.23.0.5 6379 @ mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:11.136 # +failover-state-reconf-slaves master mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:11.202 * +slave-reconf-sent slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.3 6379
redis-sentinel-3 | 1:X 26 Jul 2019 06:41:11.202 # +config-update-from sentinel 9a8f27c0b49b38cdd4df0e6b1a8698ec4e5dfc63 172.23.0.6 26379 @ mymaster 172.23.0.3 6379
redis-sentinel-3 | 1:X 26 Jul 2019 06:41:11.202 # +switch-master mymaster 172.23.0.3 6379 172.23.0.5 6379
redis-sentinel-3 | 1:X 26 Jul 2019 06:41:11.202 * +slave slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.5 6379
redis-sentinel-3 | 1:X 26 Jul 2019 06:41:11.202 * +slave slave 172.23.0.3:6379 172.23.0.3 6379 @ mymaster 172.23.0.5 6379
redis-sentinel-2 | 1:X 26 Jul 2019 06:41:11.203 # +config-update-from sentinel 9a8f27c0b49b38cdd4df0e6b1a8698ec4e5dfc63 172.23.0.6 26379 @ mymaster 172.23.0.3 6379
redis-sentinel-2 | 1:X 26 Jul 2019 06:41:11.203 # +switch-master mymaster 172.23.0.3 6379 172.23.0.5 6379
redis-sentinel-2 | 1:X 26 Jul 2019 06:41:11.203 * +slave slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.5 6379
redis-sentinel-2 | 1:X 26 Jul 2019 06:41:11.203 * +slave slave 172.23.0.3:6379 172.23.0.3 6379 @ mymaster 172.23.0.5 6379
redis-slave-1 | 1:S 26 Jul 2019 06:41:11.203 # Connection with master lost.
redis-slave-1 | 1:S 26 Jul 2019 06:41:11.203 * Caching the disconnected master state.
redis-slave-1 | 1:S 26 Jul 2019 06:41:11.203 * REPLICAOF 172.23.0.5:6379 enabled (user request from 'id=4 addr=172.23.0.6:60264 fd=9 name=sentinel-9a8f27c0-cmd age=46 idle=0 flags=x db=0 sub=0 psub=0 multi=3 qbuf=299 qbuf-free=32469 obl=36 oll=0 omem=0 events=r cmd=exec')
demoapp      | [2019-07-26 06:41:11.231][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:11.232][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:11.341][app.py:39][ERROR]Timeout reading from socket
redis-slave-1 | 1:S 26 Jul 2019 06:41:11.565 * Connecting to MASTER 172.23.0.5:6379
redis-slave-1 | 1:S 26 Jul 2019 06:41:11.565 * MASTER <-> REPLICA sync started
redis-slave-1 | 1:S 26 Jul 2019 06:41:11.565 * Non blocking connect for SYNC fired the event.
redis-slave-1 | 1:S 26 Jul 2019 06:41:11.565 * Master replied to PING, replication can continue...
redis-slave-1 | 1:S 26 Jul 2019 06:41:11.566 * Trying a partial resynchronization (request c465dda6926dad2c57e23289b0cec185a83c7d81:24375).
redis-slave-2 | 1:M 26 Jul 2019 06:41:11.566 * Replica 172.23.0.4:6379 asks for synchronization
redis-slave-2 | 1:M 26 Jul 2019 06:41:11.566 * Partial resynchronization request from 172.23.0.4:6379 accepted. Sending 617 bytes of backlog starting from offset 24375.
redis-slave-1 | 1:S 26 Jul 2019 06:41:11.566 * Successful partial resynchronization with master.
redis-slave-1 | 1:S 26 Jul 2019 06:41:11.566 # Master replication ID changed to 3dba1fcea0cab761dc959243ea26399cc93811fd
redis-slave-1 | 1:S 26 Jul 2019 06:41:11.566 * MASTER <-> REPLICA sync: Master accepted a Partial Resynchronization.
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:12.198 # -odown master mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:12.198 * +slave-reconf-inprog slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:12.198 * +slave-reconf-done slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:12.251 # +failover-end master mymaster 172.23.0.3 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:12.251 # +switch-master mymaster 172.23.0.3 6379 172.23.0.5 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:12.251 * +slave slave 172.23.0.4:6379 172.23.0.4 6379 @ mymaster 172.23.0.5 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:12.251 * +slave slave 172.23.0.3:6379 172.23.0.3 6379 @ mymaster 172.23.0.5 6379
demoapp      | [2019-07-26 06:41:12.347][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:12.348][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:12.355][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:12'
demoapp      | [2019-07-26 06:41:13.358][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:13.359][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:13.362][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:13'
demoapp      | [2019-07-26 06:41:14.365][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:14.366][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:14.369][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:14'
demoapp      | [2019-07-26 06:41:15.376][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:15.377][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:15.481][app.py:39][ERROR]Timeout reading from socket
redis-sentinel-3 | 1:X 26 Jul 2019 06:41:16.214 # +sdown slave 172.23.0.3:6379 172.23.0.3 6379 @ mymaster 172.23.0.5 6379
redis-sentinel-2 | 1:X 26 Jul 2019 06:41:16.222 # +sdown slave 172.23.0.3:6379 172.23.0.3 6379 @ mymaster 172.23.0.5 6379
demoapp      | [2019-07-26 06:41:16.485][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:16.487][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:16.490][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:16'
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:17.287 # +sdown slave 172.23.0.3:6379 172.23.0.3 6379 @ mymaster 172.23.0.5 6379
demoapp      | [2019-07-26 06:41:17.492][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:17.494][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379)]
demoapp      | [2019-07-26 06:41:17.497][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:17'

```

Using following command to unpause redis-master. redis-master (172.23.0.3) is a part of slave nodes now.
```bash
demoapp      | [2019-07-26 06:41:45.733][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:45.734][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379)]
demoapp      | [2019-07-26 06:41:45.738][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:45'
redis-master | 1:M 26 Jul 2019 06:41:45.786 # Connection with replica client id #19 lost.
redis-master | 1:M 26 Jul 2019 06:41:45.786 # Connection with replica client id #18 lost.
redis-sentinel-2 | 1:X 26 Jul 2019 06:41:45.824 # -sdown slave 172.23.0.3:6379 172.23.0.3 6379 @ mymaster 172.23.0.5 6379
redis-sentinel-3 | 1:X 26 Jul 2019 06:41:45.827 # -sdown slave 172.23.0.3:6379 172.23.0.3 6379 @ mymaster 172.23.0.5 6379
redis-sentinel-1 | 1:X 26 Jul 2019 06:41:45.842 # -sdown slave 172.23.0.3:6379 172.23.0.3 6379 @ mymaster 172.23.0.5 6379
demoapp      | [2019-07-26 06:41:46.742][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:46.743][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:46.746][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:03'
demoapp      | [2019-07-26 06:41:47.748][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:47.750][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:47.753][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:03'
demoapp      | [2019-07-26 06:41:48.755][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:48.756][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:48.759][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:03'
demoapp      | [2019-07-26 06:41:49.763][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:49.764][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:49.767][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:03'
demoapp      | [2019-07-26 06:41:50.769][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:50.770][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:50.773][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:50'
demoapp      | [2019-07-26 06:41:51.777][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:51.778][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:51.782][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:51'
demoapp      | [2019-07-26 06:41:52.803][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:52.804][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:52.807][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:52'
demoapp      | [2019-07-26 06:41:53.810][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:53.811][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:53.815][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:03'
demoapp      | [2019-07-26 06:41:54.818][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:54.819][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:54.822][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:54'
demoapp      | [2019-07-26 06:41:55.825][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:55.826][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:55.829][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:03'
redis-sentinel-2 | 1:X 26 Jul 2019 06:41:55.859 * +convert-to-slave slave 172.23.0.3:6379 172.23.0.3 6379 @ mymaster 172.23.0.5 6379
redis-master | 1:S 26 Jul 2019 06:41:55.859 * Before turning into a replica, using my master parameters to synthesize a cached master: I may be able to synchronize with the new master with just a partial transfer.
redis-master | 1:S 26 Jul 2019 06:41:55.859 * REPLICAOF 172.23.0.5:6379 enabled (user request from 'id=79 addr=172.23.0.7:38962 fd=47 name=sentinel-5389774d-cmd age=10 idle=0 flags=x db=0 sub=0 psub=0 multi=3 qbuf=150 qbuf-free=32618 obl=36 oll=0 omem=0 events=r cmd=exec')
redis-master | 1:S 26 Jul 2019 06:41:56.573 * Connecting to MASTER 172.23.0.5:6379
redis-master | 1:S 26 Jul 2019 06:41:56.573 * MASTER <-> REPLICA sync started
redis-master | 1:S 26 Jul 2019 06:41:56.573 * Non blocking connect for SYNC fired the event.
redis-master | 1:S 26 Jul 2019 06:41:56.573 * Master replied to PING, replication can continue...
redis-slave-2 | 1:M 26 Jul 2019 06:41:56.573 * Replica 172.23.0.3:6379 asks for synchronization
redis-slave-2 | 1:M 26 Jul 2019 06:41:56.574 * Partial resynchronization not accepted: Requested offset for second ID was 105537, but I can reply up to 24375
redis-slave-2 | 1:M 26 Jul 2019 06:41:56.574 * Starting BGSAVE for SYNC with target: disk
redis-slave-2 | 1:M 26 Jul 2019 06:41:56.574 * Background saving started by pid 29
redis-master | 1:S 26 Jul 2019 06:41:56.573 * Trying a partial resynchronization (request c465dda6926dad2c57e23289b0cec185a83c7d81:105537).
redis-master | 1:S 26 Jul 2019 06:41:56.574 * Full resync from master: 3dba1fcea0cab761dc959243ea26399cc93811fd:36347
redis-master | 1:S 26 Jul 2019 06:41:56.574 * Discarding previously cached master state.
redis-slave-2 | 29:C 26 Jul 2019 06:41:56.580 * DB saved on disk
redis-slave-2 | 29:C 26 Jul 2019 06:41:56.580 * RDB: 0 MB of memory used by copy-on-write
redis-master | 1:S 26 Jul 2019 06:41:56.676 * MASTER <-> REPLICA sync: receiving 8757 bytes from master
redis-slave-2 | 1:M 26 Jul 2019 06:41:56.676 * Background saving terminated with success
redis-slave-2 | 1:M 26 Jul 2019 06:41:56.676 * Synchronization with replica 172.23.0.3:6379 succeeded
redis-master | 1:S 26 Jul 2019 06:41:56.677 * MASTER <-> REPLICA sync: Flushing old data
redis-master | 1:S 26 Jul 2019 06:41:56.677 * MASTER <-> REPLICA sync: Loading DB in memory
redis-master | 1:S 26 Jul 2019 06:41:56.677 * MASTER <-> REPLICA sync: Finished with success
demoapp      | [2019-07-26 06:41:56.832][app.py:30][DEBUG]Cluster Master: ('172.23.0.5', 6379)
demoapp      | [2019-07-26 06:41:56.833][app.py:31][DEBUG]Cluster Slave: [('172.23.0.4', 6379), ('172.23.0.3', 6379)]
demoapp      | [2019-07-26 06:41:56.836][app.py:37][DEBUG]Reading key(timestamp): b'2019-07-26 06:41:56'
```

## Cleanup

Using following command to stop and clean containers.
```bash
docker-compose down
```

**Note: Please restore sentinel configuration to default after running the above command.**

## References
https://redis.io/topics/sentinel
https://medium.com/@amila922/redis-sentinel-high-availability-everything-you-need-to-know-from-dev-to-prod-complete-guide-deb198e70ea6
