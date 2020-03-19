from prometheus_client import start_http_server, Summary, Gauge
import time
import requests
import json
import logging
import threading
import stat
import datetime
import sys
import yaml
import gc
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create a file handler
# handler = logging.FileHandler('osExporter.log')
handler = logging.FileHandler('/log/osExporter.log')

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

logger.info('Starting objecteserver_exporter')
logger.info('Start gathering configuration parameters')
# ObjectServer Exporter Default Configuration (will be replaces by reading a configfile)
osLogPath = ''
osReqFreq = 30
conTimeout = 5
exitFlag = 0
logger.info('Finished gathering configuration parameters')

# Prometheus metric definitions
logger.info('Start setting prometheus metric definitions')
OS_EVENTS_TOTAL = Gauge('os_events_total', 'Total events in the Objectserver', ['hostserver', 'objectserver'])
OS_EVENTS_CRITICAL = Gauge('os_events_critical_total', 'Total critical events', ['hostserver', 'objectserver'])
OS_EVENTS_MAJOR = Gauge('os_events_major_total', 'Total major events', ['hostserver', 'objectserver'])
OS_EVENTS_MINOR = Gauge('os_events_minor_total', 'Total minor events', ['hostserver', 'objectserver'])
OS_EVENTS_WARNING = Gauge('os_events_warning_total', 'Total warning events', ['hostserver', 'objectserver'])
OS_EVENTS_INDETERMINATE = Gauge('os_events_indeterminate_total', 'Total indeterminate events', ['hostserver', 'objectserver'])
OS_EVENTS_CLEAR = Gauge('os_events_clear_total', 'Total clear events', ['hostserver', 'objectserver'])
OS_COLUMNS_TOTAL = Gauge('os_columns_total', 'Number of objectserver alerts.status columns', ['hostserver', 'objectserver'])
OS_COLUMNS_DETAILS = Gauge('os_columns_details', 'Schema Details from objecserver alerts.status', ['hostserver', 'objectserver', 'columnname', 'type', 'key'])
OS_ALERTS_DETAILS_TOTAL = Gauge('os_alerts_details_total', 'Alerts Details Total', ['hostserver', 'objectserver'])
OS_ALERTS_JOURNAL_TOTAL = Gauge('os_alerts_journal_total', 'Alerts Journal Total', ['hostserver', 'objectserver'])

OS_CONNECTIONS_TOTAL = Gauge('os_connections_total', 'Objectserver Connections Total', ['hostserver', 'objectserver'])
OS_CONNECTIONS_ISREALTIME = Gauge('os_connections_isrealtime', 'Objectserver Connections isRealTime Bool', ['hostserver', 'objectserver', 'logname', 'hostname', 'connectionappname', 'appdescription'])
OS_CONNECTIONS_CONNECTTIME = Gauge('os_connections_connecttime', 'Objectserver Connections Connecttime Total', ['hostserver', 'objectserver', 'logname', 'hostname', 'connectionappname', 'appdescription'])

OS_TRIGGER_TOTAL = Gauge('os_trigger_total', 'Total Number of Trigger in Objectserver', ['hostserver', 'objectserver'])
OS_TRIGGER_ACTIVE_TOTAL = Gauge('os_trigger_active_total', 'Total Number of active trigger in Objectserver', ['hostserver', 'objectserver'])
OS_TRIGGER_INACTIVE_TOTAL = Gauge('os_trigger_inactive_total', 'Total Number of inactive trigger in Objectserver', ['hostserver', 'objectserver'])
OS_TRIGGER_STATS_PREVIOUSROWCOUNT = Gauge('os_trigger_stats_previousrowcount', 'Number of previous row counts', ['hostserver', 'objectserver', 'trigger', 'active'])
OS_TRIGGER_STATS_NUMZEROROWCOUNT = Gauge('os_trigger_stats_numzerorowcount', 'Number of zero Row counts', ['hostserver', 'objectserver', 'trigger', 'active'])
OS_TRIGGER_STATS_NUMPOSITIVEROWCOUNT = Gauge('os_trigger_stats_numpositiverowcount', 'Number of positive Row counts', ['hostserver', 'objectserver', 'trigger', 'active'])
OS_TRIGGER_STATS_PERIODNUMRAISES = Gauge('os_trigger_stats_periodnumraises', 'Number of raises in period', ['hostserver', 'objectserver', 'trigger', 'active'])
OS_TRIGGER_STATS_PERIODNUMFIRES = Gauge('os_trigger_stats_periodnumfires', 'Number of trigger fired in period', ['hostserver', 'objectserver', 'trigger', 'active'])
OS_TRIGGER_STATS_PERIODTIME_SEC = Gauge('os_trigger_stats_periodtime_sec', 'Time in sec for this period', ['hostserver', 'objectserver', 'trigger', 'active'])
OS_TRIGGER_STATS_NUMRAISES = Gauge('os_trigger_stats_numraises', 'Number of raises', ['hostserver', 'objectserver', 'trigger', 'active'])
OS_TRIGGER_STATS_NUMFIRES = Gauge('os_trigger_stats_numfires', 'Number of fires', ['hostserver', 'objectserver', 'trigger', 'active'])
OS_TRIGGER_STATS_MAXTIME_SEC = Gauge('os_trigger_stats_maxtime_sec', 'Maximum time in sec', ['hostserver', 'objectserver', 'trigger', 'active'])
OS_TRIGGER_STATS_TOTALTIME_SEC = Gauge('os_trigger_stats_totaltime_sec', 'Total time in sec', ['hostserver', 'objectserver', 'trigger', 'active'])

OS_MEMSTORE_HARDLIMIT_BYTES = Gauge('os_memstore_hardlimit_bytes', 'Hardlimit in bytes for memstore', ['hostserver', 'objectserver', 'storename', 'isprotected'])
OS_MEMSTORE_SOFTLIMIT_BYTES = Gauge('os_memstore_softlimit_bytes', 'Softlimit in bytes for memstore', ['hostserver', 'objectserver', 'storename', 'isprotected'])
OS_MEMSTORE_USEDBYTES_BYTES = Gauge('os_memstore_usedbytes_bytes', 'Used bytes for memstore', ['hostserver', 'objectserver', 'storename', 'isprotected'])

OS_PROFILES_TOTAL_NUM = Gauge('os_profiles_total_num', 'Numer of profiles', ['hostserver', 'objectserver'])
OS_PROFILES_LASTSQLTIME_SEC = Gauge('os_profiles_lastsqltime_sec', 'Last measured SQL Time', ['hostserver', 'objectserver', 'appname', 'hostname'])
#OS_PROFILES_MINSQLTIME_SEC = Gauge('os_profiles_minsqltime_sec', 'Minimum measured SQL Time', ['hostserver', 'objectserver', 'appname', 'hostname'])
#OS_PROFILES_MAXSQLTIME_SEC = Gauge('os_profiles_maxsqltime_sec', 'Maximum measured SQL Time', ['hostserver', 'objectserver', 'appname', 'hostname'])
OS_PROFILES_PERIODSQLTIMES_SEC = Gauge('os_profiles_periodsqltime_sec', 'Measured SQL Time during period', ['hostserver', 'objectserver', 'appname', 'hostname'])
OS_PROFILES_TOTALSQLTIME_SEC = Gauge('os_profiles_totalsqltime_sec', 'Total time, in seconds, for running all SQL commands for this client.', ['hostserver', 'objetcserver', 'appname', 'hostname'])
OS_PROFILES_LASTTIMINGAT_SEC = Gauge('os_profiles_lasttimingat_sec', 'Last time an SQL profile was taken for this client.', ['hostserver', 'objectserver', 'appname', 'hostname'])
OS_PROFILES_PROFILEDFROM_SEC = Gauge('os_profiles_profiledfrom_sec', 'Time at which profiling began.', ['hostserver', 'objectserver', 'appname', 'hostname'])
OS_PROFILES_NUMSUBMITS_NUM = Gauge('os_profiles_numsubmits_num', 'Number of submissions for this client.', ['hostserver', 'objectserver', 'appname', 'hostname'])
OS_PROFILES_TOTALPARSETIME_SEC = Gauge('os_profiles_totalparsetime_sec', 'Records the total amount of time spent parsing commands for this client.', ['hostserver', 'objectserver', 'appname', 'hostname'])
OS_PROFILES_RESOLVETIME_SEC = Gauge('os_profiles_totalresolvetime_sec', 'Records the total amount of time spent resolving commands for this client.', ['hostserver', 'objectserver', 'appname', 'hostname'])
OS_PROFILES_EXECTIME_SEC = Gauge('os_profiles_totalexectime_sec', 'Records the total amount of time spent running commands for this client.', ['hostserver', 'objectserver', 'appname', 'hostname'])

#OS_MASTERSTATS_STATTIME_SEC = Gauge('os_masterstats_stattime_sec', 'The time that the statistics are collected.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_CLIENTS_NUM = Gauge('os_masterstats_clients_num', 'The total number of clients (for example, desktops) connected to the ObjectServer.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_REALTIME_NUM = Gauge('os_masterstats_realtime_num', 'The number of real-time clients connected to the ObjectServer. Desktops and gateways use IDUC and are real-time connections.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_PROBES_NUM = Gauge('os_masterstats_probes_num', 'The number of probes connected to the ObjectServer.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_GATEWAYS_NUM = Gauge('os_masterstats_gateways_num', 'The number of gateways connected to the ObjectServer.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_MONITORS_NUM = Gauge('os_masterstats_monitors_num', 'The number of monitors connected to the ObjectServer.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_PROXYS_NUM = Gauge('os_masterstats_proxys_num', 'The number of proxy servers connected to the ObjectServer.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_EVENTCOUNT_NUM = Gauge('os_masterstats_eventcount_num', 'The current number of entries in the alerts.status table.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_JOURNALCOUNT_NUM = Gauge('os_masterstats_journalcount_num', 'The current number of entries in the alerts.journal table.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_DETAILCOUNT_NUM = Gauge('os_masterstats_detailcount_num', 'The current number of entries in the alerts.details table.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_STATUSINSERTS_TOTAL = Gauge('os_masterstats_statusinserts_total', 'The total number of inserts into the alerts.status table.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_STATUSNEWINSERTS_NUM = Gauge('os_masterstats_statusnewinserts_num', 'The number of new inserts into the alerts.status table.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_STATUSDEDUPS_NUM = Gauge('os_masterstats_statusdedups_num', 'The number of reinserts into the alerts.status table.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_JOURNALINSERTS_NUM = Gauge('os_masterstats_journalinserts_num', 'The number of inserts into the alerts.journal table.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_DETAILSINSERTS_NUM = Gauge('os_masterstats_detailsinserts_num', 'The number of inserts into the alerts.details table.', ['hostserver', 'objectserver'])
OS_MASTERSTATS_STATUSUPDATES_NUM = Gauge('os_masterstats_statusupdates_num', 'The number of updates to the alerts.status table.', ['hostserver', 'objectserver'])

OS_MASTERPROBESTATS_UPTIME_NUM = Gauge('os_masterprobestats_uptime_num', 'The uptime of the probe in seconds', ['hostserver', 'objectserver', 'probeagent', 'probehost'])
OS_MASTERPROBESTATS_EVENTSPROCESSED_NUM = Gauge('os_masterprobestats_eventsprocessed_num', 'The uptime of the probe in seconds', ['hostserver', 'objectserver', 'probeagent', 'probehost'])
OS_MASTERPROBESTATS_EVENTSGENERATED_NUM = Gauge('os_masterprobestats_eventsgenerated_num', 'The uptime of the probe in seconds', ['hostserver', 'objectserver', 'probeagent', 'probehost'])
OS_MASTERPROBESTATS_EVENTSDISCARDED_NUM = Gauge('os_masterprobestats_eventsdiscarded_num', 'The uptime of the probe in seconds', ['hostserver', 'objectserver', 'probeagent', 'probehost'])
OS_MASTERPROBESTATS_RULESFILETIME_SEC = Gauge('os_masterprobestats_rulesfiletime_sec', 'The uptime of the probe in seconds', ['hostserver', 'objectserver', 'probeagent', 'probehost'])
OS_MASTERPROBESTATS_AVGRULESFILETIME_SEC = Gauge('os_masterprobestats_avgrulesfiletime_sec', 'The uptime of the probe in seconds', ['hostserver', 'objectserver', 'probeagent', 'probehost'])
OS_MASTERPROBESTATS_CPUTIME_SEC = Gauge('os_masterprobestats_cputime_sec', 'The uptime of the probe in seconds', ['hostserver', 'objectserver', 'probeagent', 'probehost'])
OS_MASTERPROBESTATS_PROBEMEMORY_NUM = Gauge('os_masterprobestats_probememory_num', 'The uptime of the probe in seconds', ['hostserver', 'objectserver', 'probeagent', 'probehost'])

# Impact SelfMonitoring
OS_IMPACT_QUEUE_SIZE_NUM = Gauge('os_impact_queue_size_num','Queue Size of an Impact',['impacthost','objectserver','queuename'])
OS_IMPACT_HEAP_USED_NUM = Gauge('os_impact_heap_used_num','Heap memory use by Impact in Megabyte',['impacthost','objectserver'])
OS_IMPACT_HEAP_MAX_NUM = Gauge('os_impact_heap_max_num','Maximum heap size available for Impact',['impacthost','objectserver'])
OS_IMPACT_SYSTEM_FREE_MEM_AIVALABLE_NUM = Gauge('os_impact_system_free_mem_available_num','Free memory available on impact server',['impacthost','objectserver'])

# WebGUI SelfMonitoring
OS_WEBGUI_SQL_AVG_RESPONSE_SEC = Gauge('os_webgui_sql_avg_response_sec','Average SQL response time in seconds',['webguihost','objectserver'])
OS_WEBGUI_SQL_MAX_RESPONSE_SEC = Gauge('os_webgui_sql_max_response_sec','Maximum SQL response time in seconds',['webguihost','objectserver'])
OS_WEBGUI_EVENT_DATA_SERVICE_AVG_RESPONSE_SEC = Gauge('os_webgui_event_data_service_avg_response_sec','Average event data service response time in seconds',['webguihost','objectserver'])
OS_WEBGUI_EVENT_DATA_SERVICE_MAX_RESPONSE_SEC = Gauge('os_webgui_event_data_service_max_response_sec','Maximum event data service response time in seconds',['webguihost','objectserver'])
OS_WEBGUI_EVENT_SUMMARY_DATA_SERVICE_AVG_RESPONSE_SEC = Gauge('os_webgui_event_summary_data_service_avg_response_sec','Average event summary data service response time in seconds',['webguihost','objectserver'])
OS_WEBGUI_EVENT_SUMMARY_DATA_SERVICE_MAX_RESPONSE_SEC = Gauge('os_webgui_event_summary_data_service_max_response_sec','Maximum event summary data service response time in seconds',['webguihost','objectserver'])
OS_WEBGUI_JVM_MAX_NUM = Gauge('os_webgui_jvm_max_num','Maximum JVM memory available in MB',['webguihost','objectserver'])
OS_WEBGUI_JVM_USAGE_NUM = Gauge('os_webgui_jvm_usage_num','JVM memory usage in MB',['webguihost','objectserver'])
OS_WEBGUI_METRIC_DATA_SERVICE_MAX_RESPONSE_SEC = Gauge('os_webgui_metric_data_service_max_response_sec','Maximum metric data service response time in seconds',['webguihost','objectserver'])
OS_WEBGUI_METRIC_DATA_SERVICE_AVG_RESPONSE_SEC = Gauge('os_webgui_metric_data_service_avg_response_sec','Average metric data service response time in seconds',['webguihost','objectserver'])
OS_WEBGUI_DATASOURCE_CACHE_SIZE_NUM = Gauge('os_webgui_datasource_cache_size_num','Datasource cache size',['webguihost','objectserver','datasource'])
OS_WEBGUI_DATASOURCE_CACHE_HITRATE_PC = Gauge('os_webgui_datasource_cache_hitrate_pc','Datasource cache hitrate per cent',['webguihost','objectserver','datasource'])
OS_WEBGUI_SECURITY_REPOSITORY_AVG_RESPONSE_SEC = Gauge('os_webgui_security_repository_avg_response_sec','Average security repository response time in seconds',['webguihost','objectserver'])
OS_WEBGUI_SECURITY_REPOSITORY_MAX_RESPONSE_SEC = Gauge('os_webgui_security_repository_max_response_sec','Maximum security repository response time in seconds',['webguihost','objectserver'])
OS_WEBGUI_VMM_AVG_RESPONSE_SEC = Gauge('os_webgui_vmm_avg_response_sec','Average vmm response time in seconds',['webguihost','objectserver'])
OS_WEBGUI_VMM_MAX_RESPONSE_SEC = Gauge('os_webgui_vmm_max_response_sec','Maximum vmm response time in seconds',['webguihost','objectserver'])

# OS Exporter Selfmonitoring
OSEXPORTER_SELF_TOTALTHREADS_NUM = Gauge('osexporter_self_totalthreads_num', 'Active Thread objects')
OSEXPORTER_SELF_OSSCRAPETIMETOTAL_SEC = Gauge('osexporter_self_osscrapetimetotal_sec', 'Time needed to scrape all data from one objectserver', ['threadname', 'hostserver', 'restport'])
OSEXPORTER_SELF_OSSCRAPETIMEALERTSSTATUS_SEC = Gauge('osexporter_self_osscrapetimealertsstatus_sec', 'Time needed to scrape all alerts.status from one objectserver', ['threadname', 'hostserver', 'restport'])
OSEXPORTER_SELF_OSSCRAPETIMEALERTSSTATUSCOLUMNS_SEC = Gauge('osexporter_self_osscrapetimealertstatuscolumns_sec', 'Time needed to scrape all alerts.status Field Details from one objectserver', ['threadname', 'hostserver', 'restport'])
OSEXPORTER_SELF_OSSCRAPETIMEMASTERSTATSROW_SEC = Gauge('osexporter_self_osscrapetimemasterstatsrow_sec', 'Time needed to scrape latest master stats info', ['threadname', 'hostserver', 'restport'])
OSEXPORTER_SELF_OSSCRAPEHTMLRETURNCODE_NUM = Gauge('osexporter_self_osscrapehtmlreturncode_num', 'The HTML Returncode from the Objectserver Rest API', ['threadname', 'hostserver', 'restport'])
OSEXPORTER_SELF_OSSCRAPETIMEMASTERPROBESTATS_SEC = Gauge('osexporter_self_osscrapetimemasterprobestats_sec', 'Time needed to scrape master.probestats info', ['threadname', 'hostserver', 'restport'])

logger.info('Finished setting prometheus metric definitions')


class myOSDataThread (threading.Thread):
    def __init__(self, threadID, name, restURL, restPort, restUser, restPW, restProbeSelfMon, restProfileDetails, restConTimeout, restImpactSelfMonitoring, restWebGUISelfMonitoring):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.restURL = restURL
        self.restPort = restPort
        self.restUser = restUser
        self.restPW = restPW
        self.probeSelfMon = restProbeSelfMon
        self.ProfileDetails = restProfileDetails
        self.restConTimeout = restConTimeout
        self.restImpactSelfMonitoring = restImpactSelfMonitoring
        self.restWebGUISelfMonitoring = restWebGUISelfMonitoring

    def run(self):
        logging.info("Starting Thread" + self.name)
        getOsData(self.name, self.restURL, self.restPort, self.restUser, self.restPW, self.probeSelfMon, self.ProfileDetails, self.restConTimeout, self.restImpactSelfMonitoring, self.restWebGUISelfMonitoring)
        logging.info("Exiting Thread" + self.name)

def getOsData(threadName, osRest, osRestPort, osLoginUser, osLoginPW, osProbeSelfMon, osProfileDetails, conTimeout, osImpactSelfMonitoring, osWebGUISelfMonitoring):
    osName = ''
    osEventsCritical = 0
    osEventsMajor = 0
    osEventsMinor = 0
    osEventsWarning = 0
    osEventsIndeterminate = 0
    osEventsClear = 0
    requestLoopCounter = 1
    # Processing Events from alerts.status
    logger.info('Start gathering data from ' + osRest + ':' + osRestPort + ' every ' + str(osReqFreq) + ' seconds')
    session = requests.Session()
    while True:
        logger.info(threadName + ': Start gathering alerts.status data from ' + osRest + ' for the ' + str(requestLoopCounter) + ' time')
        startTime = time.time()
        try:
            alertsStatusSeverity = session.post('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory', json={'sqlcmd': 'select Severity, count(*) as Total from alerts.status group by Severity'}, auth=(osLoginUser, osLoginPW))
            logger.debug(threadName + ': HTML Return Code from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory' + ' is: ' + str(alertsStatusSeverity.status_code))
            OSEXPORTER_SELF_OSSCRAPEHTMLRETURNCODE_NUM.labels(threadName, osRest, osRestPort).set(alertsStatusSeverity.status_code)

        except:
            logger.error('Getting alert.status from ' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/status failed', exc_info=True)
        try:
            osAlertsStatusSeverity = alertsStatusSeverity.json()
            for event in osAlertsStatusSeverity['rowset']['rows']:
                if event['Severity'] == 5:
                    osEventsCritical = event['Total']
                if event['Severity'] == 4:
                    osEventsMajor = event['Total']
                if event['Severity'] == 3:
                    osEventsMinor = event['Total']
                if event['Severity'] == 2:
                    osEventsWarning = event['Total']
                if event['Severity'] == 1:
                    osEventsIndeterminate = event['Total']
                if event['Severity'] == 0:
                    osEventsClear = event['Total']
            osEventsTotal = osEventsCritical + osEventsMajor + osEventsMinor + osEventsWarning + osEventsIndeterminate + osEventsClear
            OS_EVENTS_TOTAL.labels(osRest, osAlertsStatusSeverity['rowset']['osname']).set(osEventsTotal)
            OS_EVENTS_CRITICAL.labels(osRest, osAlertsStatusSeverity['rowset']['osname']).set(osEventsCritical)
            OS_EVENTS_MAJOR.labels(osRest, osAlertsStatusSeverity['rowset']['osname']).set(osEventsMajor)
            OS_EVENTS_MINOR.labels(osRest, osAlertsStatusSeverity['rowset']['osname']).set(osEventsMinor)
            OS_EVENTS_WARNING.labels(osRest, osAlertsStatusSeverity['rowset']['osname']).set(osEventsWarning)
            OS_EVENTS_INDETERMINATE.labels(osRest, osAlertsStatusSeverity['rowset']['osname']).set(osEventsIndeterminate)
            OS_EVENTS_CLEAR.labels(osRest, osAlertsStatusSeverity['rowset']['osname']).set(osEventsClear)
            alertsStatusTime = time.time() - startTime
            OSEXPORTER_SELF_OSSCRAPETIMEALERTSSTATUS_SEC.labels(threadName, osRest, osRestPort).set(alertsStatusTime)
            logger.debug(threadName + ': Finished gathering data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/status in ' + str(alertsStatusTime) + ' seconds')
        except:
            logger.error('Converting JSON into alerts.status metrics failed', exc_info=True)
        alertsStatusSeverity = {}
        osAlertsStatusSeverity = {}

        # Gathering alerts.status Schema Details
        if requestLoopCounter == 1 or requestLoopCounter % 10 == 1:
            startTimeAlertsStatusColumns = time.time()
            try:
                alertsColumnsDetails = session.post('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory', json={'sqlcmd': 'describe alerts.status'}, auth=(osLoginUser, osLoginPW))
                logger.debug(threadName + ': HTML Return Code for alerts.status Schema from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory' + ' is: ' + str(alertsColumnsDetails.status_code))

            except:
                logger.error('Getting alert.status Schema Data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory failed', exc_info=True)
            try:
                osAlertsColumnsDetails = alertsColumnsDetails.json()
                OS_COLUMNS_TOTAL.labels(osRest, osAlertsColumnsDetails['rowset']['osname']).set(osAlertsColumnsDetails['rowset']['affectedRows'])
                for column in osAlertsColumnsDetails['rowset']['rows']:
                    OS_COLUMNS_DETAILS.labels(osRest, osAlertsColumnsDetails['rowset']['osname'], column['ColumnName'], column['Type'], column['Key']).set(column['Size'])

                alertsColumnsTime = time.time() - startTimeAlertsStatusColumns
                OSEXPORTER_SELF_OSSCRAPETIMEALERTSSTATUSCOLUMNS_SEC.labels(threadName, osRest, osRestPort).set(alertsColumnsTime)
                logger.debug(threadName + ': Finished gathering alerts.status Schema data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory in ' + str(alertsStatusTime) + ' seconds')
            except:
                logger.error('Converting JSON into alerts.status Schema metrics failed', exc_info=True)
        alertsColumnsDetails = {}
        osAlertsColumnsDetails = {}

        # Gathering latest master.stats row
        startTimeMasterStatsRow = time.time()
        try:
            masterStatsRow = session.post('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory', json={'sqlcmd': 'select TOP 1 * from master.stats order by StatTime desc'}, auth=(osLoginUser, osLoginPW))
            logger.debug(threadName + ': HTML Return Code for master.stats Schema from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory' + ' is: ' + str(masterStatsRow.status_code))

        except:
            logger.error('Getting master.stats Data from http://' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory failed', exc_info=True)
        try:
            osMasterStatsRow = masterStatsRow.json()
            for stats in osMasterStatsRow['rowset']['rows']:
                #OS_MASTERSTATS_STATTIME_SEC.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['StatTime'])
                OS_MASTERSTATS_CLIENTS_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['NumClients'])
                OS_MASTERSTATS_REALTIME_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['NumRealtime'])
                OS_MASTERSTATS_PROBES_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['NumProbes'])
                OS_MASTERSTATS_GATEWAYS_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['NumGateways'])
                OS_MASTERSTATS_MONITORS_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['NumMonitors'])
                OS_MASTERSTATS_PROXYS_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['NumProxys'])
                OS_MASTERSTATS_EVENTCOUNT_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['EventCount'])
                OS_MASTERSTATS_JOURNALCOUNT_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['JournalCount'])
                OS_MASTERSTATS_DETAILCOUNT_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['DetailCount'])
                OS_MASTERSTATS_STATUSINSERTS_TOTAL.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['StatusInserts'])
                OS_MASTERSTATS_STATUSNEWINSERTS_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['StatusNewInserts'])
                OS_MASTERSTATS_STATUSDEDUPS_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['StatusDedups'])
                OS_MASTERSTATS_JOURNALINSERTS_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['JournalInserts'])
                OS_MASTERSTATS_DETAILSINSERTS_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['DetailsInserts'])
                OS_MASTERSTATS_STATUSUPDATES_NUM.labels(osRest, osMasterStatsRow['rowset']['osname']).set(stats['StatusUpdates'])

            masterStatsRowTime = time.time() - startTimeMasterStatsRow
            OSEXPORTER_SELF_OSSCRAPETIMEMASTERSTATSROW_SEC.labels(threadName, osRest, osRestPort).set(masterStatsRowTime)
            logger.debug(threadName + ': Finished gathering master.stats data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory in ' + str(alertsStatusTime) + ' seconds')
        except:
            logger.error('Converting JSON into master.stats Schema metrics failed', exc_info=True)
        masterStatsRow = {}
        osMasterStatsRow = {}

        # Gathering Probe selfmonitoring stats
        # WARNING: Have to installed and activated on Objectserver and Probes!
        # https://www.ibm.com/support/knowledgecenter/en/SSSHTQ_8.1.0/com.ibm.netcool_OMNIbus.doc_8.1.0/omnibus/wip/probegtwy/concept/omn_prb_enablingroi.html
        if osProbeSelfMon == '1' and (osReqFreq * requestLoopCounter) % 60 == 0:
            startTimeMasterProbeStats = time.time()
            try:
                masterProbeStats = session.post('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory', json={'sqlcmd': 'select * from master.probestats'}, auth=(osLoginUser, osLoginPW))
                logger.debug(threadName + ': HTML Return Code for master.probestats from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory' + ' is: ' + str(masterStatsRow.status_code))
            except:
                logger.error('Getting master.probestats Data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory failed', exc_info=True)
            try:
                osMasterProbeStats = masterProbeStats.json()
                for probestats in osMasterProbeStats['rowset']['rows']:
                    OS_MASTERPROBESTATS_UPTIME_NUM.labels(osRest, osMasterProbeStats['rowset']['osname'], probestats['ProbeAgent'].probestats['ProbeHost']).set(probestats['ProbeUpTime'])
                    OS_MASTERPROBESTATS_EVENTSPROCESSED_NUM.labels(osRest, osMasterProbeStats['rowset']['osname'], probestats['ProbeAgent'].probestats['ProbeHost']).set(probestats['NumEventsProcessed'])
                    OS_MASTERPROBESTATS_EVENTSGENERATED_NUM.labels(osRest, osMasterProbeStats['rowset']['osname'], probestats['ProbeAgent'].probestats['ProbeHost']).set(probestats['NumEventsGenerated'])
                    OS_MASTERPROBESTATS_EVENTSDISCARDED_NUM.labels(osRest, osMasterProbeStats['rowset']['osname'], probestats['ProbeAgent'].probestats['ProbeHost']).set(probestats['NumEventsDiscarded'])
                    OS_MASTERPROBESTATS_RULESFILETIME_SEC.labels(osRest, osMasterProbeStats['rowset']['osname'], probestats['ProbeAgent'].probestats['ProbeHost']).set(probestats['RulesFileTimeSec'])
                    OS_MASTERPROBESTATS_AVGRULESFILETIME_SEC.labels(osRest, osMasterProbeStats['rowset']['osname'], probestats['ProbeAgent'].probestats['ProbeHost']).set(probestats['AvgRulesFileTime'])
                    OS_MASTERPROBESTATS_CPUTIME_SEC.labels(osRest, osMasterProbeStats['rowset']['osname'], probestats['ProbeAgent'].probestats['ProbeHost']).set(probestats['CPUTimeSec'])
                    OS_MASTERPROBESTATS_PROBEMEMORY_NUM.labels(osRest, osMasterProbeStats['rowset']['osname'], probestats['ProbeAgent'].probestats['ProbeHost']).set(probestats['ProbeMemory'])
                masterProbeStatsTime = time.time() - startTimeMasterProbeStats
                OSEXPORTER_SELF_OSSCRAPETIMEMASTERPROBESTATS_SEC.labels(threadName, osRest, osRestPort).set(masterStatsRowTime)
                logger.debug(threadName + ': Finished gathering master.probestats data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory in ' + str(alertsStatusTime) + ' seconds')
            except:
                logger.error('Converting JSON into master.probestats Schema metrics failed', exc_info=True)
            masterProbeStats = {}
            osMasterProbeStats = {}
        else:
            if osProbeSelfMon != '1':
                logger.debug('ProbeSelfmonitoring is not activated for ' + osRest + ':' + osRestPort)

        if osProfileDetails == '1':
            # Processing Profiles
            startProfilesTime = time.time()
            try:
                thisData = session.get('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/catalog/profiles', auth=(osLoginUser, osLoginPW), timeout=conTimeout)
                osProfiles = thisData.json()
                OS_PROFILES_TOTAL_NUM.labels(osRest, osProfiles['rowset']['osname']).set(osProfiles['rowset']['affectedRows'])
                for profile in osProfiles['rowset']['rows']:
                    OS_PROFILES_LASTSQLTIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['AppName'], profile['HostName']).set(profile['LastSQLTime'])
                    #OS_PROFILES_MINSQLTIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['AppName'], profile['HostName']).set(profile['MinSQLTime'])
                    #OS_PROFILES_MAXSQLTIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['AppName'], profile['HostName']).set(profile['MaxSQLTime'])
                    OS_PROFILES_PERIODSQLTIMES_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['AppName'], profile['HostName']).set(profile['PeriodSQLTime'])
                    OS_PROFILES_TOTALSQLTIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['AppName'], profile['HostName']).set(profile['TotalSQLTime'])
                    OS_PROFILES_LASTTIMINGAT_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['AppName'], profile['HostName']).set(profile['LastTimingAt'])
                    OS_PROFILES_PROFILEDFROM_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['AppName'], profile['HostName']).set(profile['ProfiledFrom'])
                    OS_PROFILES_NUMSUBMITS_NUM.labels(osRest, osProfiles['rowset']['osname'], profile['AppName'], profile['HostName']).set(profile['NumSubmits'])
                    OS_PROFILES_TOTALPARSETIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['AppName'], profile['HostName']).set(profile['TotalParseTime'])
                    OS_PROFILES_RESOLVETIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['AppName'], profile['HostName']).set(profile['TotalResolveTime'])
                    OS_PROFILES_EXECTIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['AppName'], profile['HostName']).set(profile['TotalExecTime'])
                    profilesTime = time.time() - startTime
            except:
                logger.error('Converting converting JSON into profile metrics failed')
            profiles = {}
            osProfiles = {}

            # Processing Details
            try:
                alertsDetails = session.post('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory', json={'sqlcmd': 'select count(*) as rowcount from alerts.details'}, auth=(osLoginUser, osLoginPW), timeout=conTimeout)
            except:
                logger.error('Getting data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/details failed', exc_info=True)
            try:
                osAlertsDetails = alertsDetails.json()
                for detail in osAlertsDetails['rowset']['rows']:
                    detailsTotal = detail['rowcount']
                OS_ALERTS_DETAILS_TOTAL.labels(osRest, osAlertsDetails['rowset']['osname']).set(detailsTotal)
            except:
                logger.error('Converting converting JSON for details metrics failed')
            alertsDetails = {}
            osAlertsDetails = {}
        else:
            if osProfileDetails != '1':
                logger.debug('Profile monitoring is not activated for ' + osRest + ':' + osRestPort)

        # Processsing Journal entrys
        try:
            alertsJournal = session.post('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory', json={'sqlcmd': 'select count(*) as rowcount from alerts.journal'}, auth=(osLoginUser, osLoginPW), timeout=conTimeout)
        except:
            logger.error('Getting data alerts.journal data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory failed', exc_info=True)
        try:
            osAlertsJournal = alertsJournal.json()
            for journal in osAlertsJournal['rowset']['rows']:
                journalTotal = journal['rowcount']
            OS_ALERTS_JOURNAL_TOTAL.labels(osRest, osAlertsJournal['rowset']['osname']).set(journalTotal)
        except:
            logger.error('Converting converting JSON into journal metrics failed')
        alertsJournal = {}
        osAlertsJournal = {}

        if osImpactSelfMonitoring == '1':
            # Processsing Impact Queue Selfmonitoring via Objectserver
            try:
                alertsImpactQueue = session.post('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory', json={'sqlcmd': 'select Summary, Node from alerts.status where Agent = \'Impact SelfMonitoring\' and AlertGroup = \'QueueStatus\''}, auth=(osLoginUser, osLoginPW), timeout=conTimeout)
            except:
                logger.error('Getting alerts.status Impact Event data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory failed', exc_info=True)
            try:
                osAlertsImpactQueue = alertsImpactQueue.json()
                for queues in osAlertsImpactQueue['rowset']['rows']:
                    summary = queues['Summary']
                    match = re.search('(.*) :  QueueSize: ([0-9]+).*',summary)
                    OS_IMPACT_QUEUE_SIZE_NUM.labels(queues['Node'],osAlertsImpactQueue['rowset']['osname'],match.group(1)).set(match.group(2))
                    #print('Impact Queue Node: ' + queues['Node'] + ' | Queuename: ' + match.group(1) + ' | Queuesize: ' + match.group(2))
            except:
                logger.error('Converting converting JSON into Impact Queue metrics failed')
            osAlertsImpactQueue = {}
            alertsImpactQueue = {}

            # Processsing Impact Heap Selfmonitoring via Objectserver
            try:
                alertsImpactHeap = session.post('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory', json={'sqlcmd': 'select Summary, Node from alerts.status where Agent = \'Impact SelfMonitoring\' and AlertGroup = \'MemoryStatus\''}, auth=(osLoginUser, osLoginPW), timeout=conTimeout)
            except:
                logger.error('Getting alerts.status Impact Heap data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory failed', exc_info=True)
            try:
                osAlertsImpactHeap = alertsImpactHeap.json()
                for heaps in osAlertsImpactHeap['rowset']['rows']:
                    summary = heaps['Summary']
                    match = re.search('.*using ([0-9]+)M out of ([0-9]+)M.*Available: ([0-9]+)M.*',summary)
                    OS_IMPACT_HEAP_USED_NUM.labels(heaps['Node'],osAlertsImpactHeap['rowset']['osname']).set(match.group(1))
                    OS_IMPACT_HEAP_MAX_NUM.labels(heaps['Node'],osAlertsImpactHeap['rowset']['osname']).set(match.group(2))
            except:
                logger.error('Converting converting JSON into Impact Heap metrics failed')
            osAlertsImpactHeap = {}
            alertsImpactHeap = {}

        if osWebGUISelfMonitoring == '1':
            # Processsing Impact Queue Selfmonitoring via Objectserver
            try:
                alertswebGUI = session.post('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory', json={'sqlcmd': 'select Summary, Node, AlertKey from alerts.status where AlertGroup = \'WebGUI Status\' and Type = 13'}, auth=(osLoginUser, osLoginPW), timeout=conTimeout)
            except:
                logger.error('Getting alerts.status WebGUI Event data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/sql/factory failed', exc_info=True)
            try:
                osAlertswebGUI = alertswebGUI.json()
                for webguialerts in osAlertswebGUI['rowset']['rows']:
                    webguiAlertKey = webguialerts['AlertKey']
                    if webguiAlertKey == 'DataSourceCommand':
                            summary = webguialerts['Summary']
                            if "response" in summary:
                                match = re.search('.*SQL command (.*) response time: (.*) secs',summary)
                                if 'average' in match.group(1):
                                    OS_WEBGUI_SQL_AVG_RESPONSE_SEC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(match.group(2))
                                if 'maximum' in match.group(1):
                                    OS_WEBGUI_SQL_MAX_RESPONSE_SEC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(match.group(2))
                    elif webguiAlertKey == 'EventData':
                            summary = webguialerts['Summary']
                            match = re.search('.*Event Data Service (.*) response time: (.*) secs',summary)
                            if 'average' in match.group(1):
                                OS_WEBGUI_EVENT_DATA_SERVICE_AVG_RESPONSE_SEC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(match.group(2))
                            if 'maximum' in match.group(1):
                                OS_WEBGUI_EVENT_DATA_SERVICE_MAX_RESPONSE_SEC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(match.group(2))
                    elif webguiAlertKey == 'EventSummaryData':
                            summary = webguialerts['Summary']
                            match = re.search('.*Summary Data Service (.*) response time: (.*) secs',summary)
                            if 'average' in match.group(1):
                                OS_WEBGUI_EVENT_SUMMARY_DATA_SERVICE_AVG_RESPONSE_SEC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(match.group(2))
                            if 'maximum' in match.group(1):
                                OS_WEBGUI_EVENT_SUMMARY_DATA_SERVICE_MAX_RESPONSE_SEC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(match.group(2))
                    elif webguiAlertKey == 'JVM':
                            summary = webguialerts['Summary']
                            match = re.search('JVM.*is ([0-9]+|[0-9]+\,[0-9]+) MB.* ([0-9]+|[0-9]+\,[0-9]+) MB.*',summary)
                            jvmusage = match.group(1).replace(',','')
                            jvmmax = match.group(2).replace(',','')
                            OS_WEBGUI_JVM_USAGE_NUM.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(jvmusage)
                            OS_WEBGUI_JVM_MAX_NUM.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(jvmmax)
                    elif webguiAlertKey == 'MetricData':
                            summary = webguialerts['Summary']
                            match = re.search('.*Metric Data Service (.*) response time: (.*) secs',summary)
                            if 'average' in match.group(1):
                                OS_WEBGUI_METRIC_DATA_SERVICE_AVG_RESPONSE_SEC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(match.group(2))
                            if 'maximum' in match.group(1):
                                OS_WEBGUI_METRIC_DATA_SERVICE_MAX_RESPONSE_SEC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(match.group(2))
                    elif webguiAlertKey == 'ResultsCache':
                            summary = webguialerts['Summary']
                            match = re.search('([A-Z1-9]+) cache.* ([0-9]+),.*: ([0-9]+)%',summary)
                            OS_WEBGUI_DATASOURCE_CACHE_SIZE_NUM.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname'],match.group(1)).set(match.group(2))
                            OS_WEBGUI_DATASOURCE_CACHE_HITRATE_PC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname'],match.group(1)).set(match.group(3))
                    elif webguiAlertKey == 'SecurityRepository':
                            summary = webguialerts['Summary']
                            match = re.search('.*Security Repository (.*) response time: (.*) secs',summary)
                            if 'average' in match.group(1):
                                OS_WEBGUI_SECURITY_REPOSITORY_AVG_RESPONSE_SEC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(match.group(2))
                            if 'maximum' in match.group(1):
                                OS_WEBGUI_SECURITY_REPOSITORY_MAX_RESPONSE_SEC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(match.group(2))
                    elif webguiAlertKey == 'VMM':
                            summary = webguialerts['Summary']
                            match = re.search('VMM sync (.*) response .*time: (.*) secs',summary)
                            if 'average' in match.group(1):
                                OS_WEBGUI_VMM_AVG_RESPONSE_SEC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(match.group(2))
                            if 'maximum' in match.group(1):
                                OS_WEBGUI_VMM_MAX_RESPONSE_SEC.labels(webguialerts['Node'],osAlertswebGUI['rowset']['osname']).set(match.group(2))
                    else:
                        logger.error('Error converting WebGUI Status Alerts, unknown AlertKey: ' +  webguialerts['AlertKey'])
            except:
                logger.error('Converting converting JSON into WebGUI metrics failed')
            osAlertsImpactQueue = {}
            alertsImpactQueue = {}

        # Processing Connections
        thisData = session.get('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/catalog/connections', auth=(osLoginUser, osLoginPW), timeout=conTimeout)
        try:
            osConnections = thisData.json()
            OS_CONNECTIONS_TOTAL.labels(osRest, osConnections['rowset']['osname']).set(osConnections['rowset']['affectedRows'])
            #for connection in osConnections['rowset']['rows']:
            #    OS_CONNECTIONS_ISREALTIME.labels(osRest, osConnections['rowset']['osname'], connection['LogName'], connection['HostName'], connection['AppName'], connection['AppDescription'], connection['ConnectionID']).set(connection['IsRealTime'])
            #    OS_CONNECTIONS_CONNECTTIME.labels(osRest, osConnections['rowset']['osname'], connection['LogName'], connection['HostName'], connection['AppName'], connection['AppDescription'], connection['ConnectionID']).set(connection['ConnectTime'])
        except:
            logger.error('Converting converting JSON into connection metrics failed')
        connections = {}
        osConnections = {}

        try:
            thisData = session.get('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/catalog/memstores', auth=(osLoginUser, osLoginPW), timeout=conTimeout)
            osMemstores = thisData.json()
            for memstore in osMemstores['rowset']['rows']:
                OS_MEMSTORE_HARDLIMIT_BYTES.labels(osRest, osMemstores['rowset']['osname'], memstore['StoreName'], memstore['IsProtected']).set(memstore['HardLimit'])
                OS_MEMSTORE_SOFTLIMIT_BYTES.labels(osRest, osMemstores['rowset']['osname'], memstore['StoreName'], memstore['IsProtected']).set(memstore['SoftLimit'])
                OS_MEMSTORE_USEDBYTES_BYTES.labels(osRest, osMemstores['rowset']['osname'], memstore['StoreName'], memstore['IsProtected']).set(memstore['UsedBytes'])
        except:
            logger.error('Converting converting JSON into memstore metrics failed')
        memstores = {}
        osMemstores = {}

        # Trigger Processing
        osTriggerActiveCount = 0
        osTriggerInactiveCount = 0

        try:
            thisData = session.get('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/catalog/trigger_stats', auth=(osLoginUser, osLoginPW), timeout=conTimeout)
            osTriggerStats = thisData.json()
            OS_TRIGGER_TOTAL.labels(osRest, osTriggerStats['rowset']['osname']).set(osTriggerStats['rowset']['affectedRows'])
            for trigger in osTriggerStats['rowset']['rows']:
                if trigger['PreviousCondition']:
                    osTriggerActiveCount += 1
                else:
                    osTriggerInactiveCount += 1

                OS_TRIGGER_STATS_PREVIOUSROWCOUNT.labels(osRest, osTriggerStats['rowset']['osname'], trigger['TriggerName'], trigger['PreviousCondition']).set(trigger['PreviousRowcount'])
                OS_TRIGGER_STATS_NUMZEROROWCOUNT.labels(osRest, osTriggerStats['rowset']['osname'], trigger['TriggerName'], trigger['PreviousCondition']).set(trigger['NumZeroRowcount'])
                OS_TRIGGER_STATS_NUMPOSITIVEROWCOUNT.labels(osRest, osTriggerStats['rowset']['osname'], trigger['TriggerName'], trigger['PreviousCondition']).set(trigger['NumPositiveRowcount'])
                OS_TRIGGER_STATS_PERIODNUMRAISES.labels(osRest, osTriggerStats['rowset']['osname'], trigger['TriggerName'], trigger['PreviousCondition']).set(trigger['PeriodNumRaises'])
                OS_TRIGGER_STATS_PERIODNUMFIRES.labels(osRest, osTriggerStats['rowset']['osname'], trigger['TriggerName'], trigger['PreviousCondition']).set(trigger['PeriodNumFires'])
                OS_TRIGGER_STATS_PERIODTIME_SEC.labels(osRest, osTriggerStats['rowset']['osname'], trigger['TriggerName'], trigger['PreviousCondition']).set(trigger['PeriodTime'])
                OS_TRIGGER_STATS_NUMRAISES.labels(osRest, osTriggerStats['rowset']['osname'], trigger['TriggerName'], trigger['PreviousCondition']).set(trigger['NumRaises'])
                OS_TRIGGER_STATS_NUMFIRES.labels(osRest, osTriggerStats['rowset']['osname'], trigger['TriggerName'], trigger['PreviousCondition']).set(trigger['NumFires'])
                OS_TRIGGER_STATS_MAXTIME_SEC.labels(osRest, osTriggerStats['rowset']['osname'], trigger['TriggerName'], trigger['PreviousCondition']).set(trigger['MaxTime'])
                OS_TRIGGER_STATS_TOTALTIME_SEC.labels(osRest, osTriggerStats['rowset']['osname'], trigger['TriggerName'], trigger['PreviousCondition']).set(trigger['TotalTime'])

            OS_TRIGGER_ACTIVE_TOTAL.labels(osRest, osTriggerStats['rowset']['osname']).set(osTriggerActiveCount)
            OS_TRIGGER_INACTIVE_TOTAL.labels(osRest, osTriggerStats['rowset']['osname']).set(osTriggerInactiveCount)
        except:
            logger.error('Converting converting JSON into trigger_stats metrics failed')
        triggerStats = {}
        osTriggerStats = {}

        totalTime = time.time() - startTime
        OSEXPORTER_SELF_OSSCRAPETIMETOTAL_SEC.labels(threadName, osRest, osRestPort).set(totalTime)
        logger.info(threadName + ': Finished gathering data from ' + osRest + ':' + osRestPort + ' for the ' + str(requestLoopCounter) + ' time in ' + str(totalTime) + ' seconds')
        requestLoopCounter = requestLoopCounter + 1
        if exitFlag:
            threadName.exit()
        time.sleep(osReqFreq)


if __name__ == '__main__':
    # Reading Config File
    logger.info('Reading initial config from os_exporter_cfg.yml')
    try:
        with open("/cfg/os_exporter_cfg.yml", 'r') as ymlfile:
        # with open("os_exporter_cfg.yml", 'r') as ymlfile:
            exportercfg = yaml.load(ymlfile)
    except:
        logger.error('Error Reading configfile')
        print('Error Reading configfile')

    logger.info('Finished reading the following configuration:')
    # logging config from config file
    logger.info('os_exporter config: ' + str(exportercfg['os_exporter']))
    logger.info('objectserver config: ' + str(exportercfg['objectservers']))

    exporterPort = exportercfg['os_exporter']['port']

    # Start up the server to expose the metrics.
    logger.info('Starting HTTP Server on port: ' + str(exporterPort))
    try:
        start_http_server(exporterPort)
    except:
        logger.error('HTTP Server not started on port ' + str(exporterPort), exc_info=True)

    # create new threads and start them
    oscounter = 0
    logger.info('Starting threads')
    osThreads = []
    for objectserver in exportercfg['objectservers']:
        oscounter = oscounter + 1
        threadname = 'thread_' + str(objectserver['address']) + '_' + str(objectserver['port'])
        thread = myOSDataThread(oscounter, threadname, str(objectserver['address']), str(objectserver['port']), str(objectserver['user']), str(objectserver['pw']), str(objectserver['probeSelfMon']), str(objectserver['profileDetails']), int(exportercfg['os_exporter']['contimeout']), str(objectserver['ImpactSelfMonitoring']), str(objectserver['WebGUISelfMonitoring']))
        osThreads.append(thread)
        thread.start()
        time.sleep(osReqFreq / len(exportercfg['objectservers']))

    logger.info('Threads started')
    logger.info('Active Thread objects: ' + str(threading.activeCount()))
    logger.info('Thread objects in callers thread control: ' + str(threading.currentThread()))
    logger.info('Starting Main Loop')

    # main loop
    while True:
        threadActiveCounts = threading.activeCount()
        OSEXPORTER_SELF_TOTALTHREADS_NUM.set(threadActiveCounts)
        logger.debug('Active Thread objects: ' + str(threadActiveCounts))
        logger.debug('Thread objects in callers thread control: ' + str(threading.enumerate()))
        gc.collect()
        time.sleep(30)
