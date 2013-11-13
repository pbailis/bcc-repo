
from os import system



def replace(f, orig, new):
    system("sed -i 's/%s/%s/g' %s" % (orig, new, f))

config = "/tmp/current_tpcc_config.xml"
serial_isolation = "TRANSACTION_SERIALIZABLE"
ru_isolation = "TRANSACTION_READ_UNCOMMITTED"

def setup_config(isolation, terminals, scale):
    system("cp config/base_tpcc_config.xml "+config)
    replace(config, "ISOLATION", isolation)
    replace(config, "TERMINALS", terminals)
    replace(config, "SCALE", scale)

def start_postgres(standard):
    system("sudo pkill postgres; sleep 5")
    if standard:
        system("sudo /etc/init.d/postgresql start")

    else:
        system("sudo su -l postgres -c '/usr/local/pgsql/bin/postgres -D /mnt/md0/postgresql/9.3/main -c config_file=/etc/postgresql/9.3/main/postgresql.conf &'")

def run_benchmark(outfile, standardrun):
    system("./oltpbenchmark -b tpcc%s -c %s --create=true --load=true --execute=true -s 5 -o outputfile" % ("" if standardrun else "_ru", config))
    system("mv outputfile.res %s" % (outfile))

system("rm -rf output; mkdir output")

for terminals in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]:
    for isolation in [serial_isolation, ru_isolation]:
        setup_config(isolation, terminals, 1)
        start_postgres(isolation == serial_isolation)
        run_benchmark("output/TERMINALS%d-%s" % (terminals, isolation), isolation==serial_isolation)
