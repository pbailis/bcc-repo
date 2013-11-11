java -Xmx1024m -cp `run/classpath.sh` -Dlog4j.configuration=log4j.properties com.oltpbenchmark.DBWorkload -b tpcc -c config/sample_tpcc_config.xml  --execute true

