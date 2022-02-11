import os,json,re

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_mapr_installed_packages(host):
    for p in [
        "mapr-zookeeper",
        "mapr-cldb",
        "mapr-fileserver",
        "mapr-resourcemanager",
        "mapr-historyserver",
        "mapr-nodemanager",
        "mapr-core",
        "mapr-core-internal",
        "mapr-mapreduce2",
        "mapr-zk-internal",
        "mapr-spark",
        "mapr-oozie",
        "mapr-librdkafka",
        "mapr-hadoop-core",
        "mapr-spark-historyserver",
        "mapr-oozie-internal"
    ]:
        assert host.package(p).is_installed


def test_mapr_not_installed_packages(host):
    for p in [
        "mapr-nfs",
        "mapr-gateway",
        "mapr-posix-client-basic",
        "mapr-posix-client-platinum"
    ]:
        assert not host.package(p).is_installed


def test_mapr_configfiles(host):
    for f in [
        "maprserverticket",
        "cldb.key",
        ".customSecure",
        "ssl_keystore",
        "ssl_truststore",
        "ssl_truststore.pem"
    ]:
        assert host.file("/opt/mapr/conf/" + f).exists

def test_mapr_hadoop_configfiles(host):
    source_folder = "/opt/mapr/hadoop/hadoop-2.7.0/etc/hadoop/"
    for f in [
            "core-site.xml",
            "yarn-site.xml"
            ]:
        assert host.file(source_folder + f).exists

def test_service_started(host):
    assert host.service("mapr-zookeeper").is_running
    assert host.service("mapr-warden").is_running

def test_hadoop_fs(host):
    cmd = host.run("echo mapr | maprlogin password -user mapr")
    assert "MapR credentials of user 'mapr' for cluster 'molecule-cluster' are written to" in cmd.stdout
    cmd = host.run("hadoop fs -ls -d /user/mapr")
    cmd_dir_pattern = re.compile(ur'(drwx.*mapr mapr.*/user/mapr)')
    assert re.findall(cmd_dir_pattern, cmd.stdout)

def helper_test_yarn_application(host):
    apps = host.run("curl -u mapr:mapr --cacert /opt/mapr/conf/ssl_truststore.pem -X GET -H \"Content-Type:application/json\" https://basic-core:8090/ws/v1/cluster/apps")
    state = sorted(json.loads(apps.stdout)['apps']['app'], key=lambda k: k['startedTime'], reverse=True)[0]['finalStatus']
    assert state == "SUCCEEDED"

def test_yarn(host):
    host.run("/opt/mapr/hadoop/hadoop-2.7.0/bin/yarn jar /opt/mapr/hadoop/hadoop-2.7.0/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.0-mapr-1808.jar pi 5 10")
    helper_test_yarn_application(host)

def test_hadoop(host):
    host.run("hadoop jar /opt/mapr/hadoop/hadoop-2.7.0/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.0-mapr-1808.jar pi 5 10")
    helper_test_yarn_application(host)
