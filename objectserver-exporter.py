from prometheus_client import start_http_server, Summary, Gauge, Info
import time
import requests
import json
import logging
import threading
import stat
import datetime
import sys
import yaml

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create a file handler
handler = logging.FileHandler('/log/osExporter.log')

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

logger.info('Starting objecteserver_exporter')
logger.info('Start gathering configuration parameters')
# ObjectServer Exporter Configuration (will be replaces by reading a configfile)
osLogPath = ''
osReqFreq = 30
conTimeout = 35
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
OS_COLS_TOTAL = Gauge('os_columns_total', 'Number of objectserver columns', ['hostserver', 'objectserver'])
OS_NAME = Info('os_name', 'Objecserver name')
OS_ALERTS_DETAILS_TOTAL = Gauge('os_alerts_details_total', 'Alerts Details Total', ['hostserver', 'objectserver'])
OS_ALERTS_JOURNAL_TOTAL = Gauge('os_alerts_journal_total', 'Alerts Journal Total', ['hostserver', 'objectserver'])
OS_CONNECTIONS_TOTAL = Gauge('os_connections_total', 'Objectserver Connections Total', ['hostserver', 'objectserver'])
OS_CONNECTIONS_ISREALTIME = Gauge('os_connections_isrealtime', 'Objectserver Connections isRealTime Bool', ['hostserver', 'objectserver', 'logname', 'hostname', 'appname'])
OS_CONNECTIONS_CONNECTTIME = Gauge('os_connections_connecttime', 'Objectserver Connections Connecttime Total', ['hostserver', 'objectserver', 'logname', 'hostname', 'appname'])
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
OS_PROFILES_LASTSQLTIME_SEC = Gauge('os_profiles_lastsqltime_sec', 'Last measured SQL Time', ['hostserver', 'objectserver', 'connectionid', 'uid', 'appname', 'hostname'])
OS_PROFILES_MINSQLTIME_SEC = Gauge('os_profiles_minsqltime_sec', 'Minimum measured SQL Time', ['hostserver', 'objectserver', 'connectionid', 'uid', 'appname', 'hostname'])
OS_PROFILES_MAXSQLTIME_SEC = Gauge('os_profiles_maxsqltime_sec', 'Maximum measured SQL Time', ['hostserver', 'objectserver', 'connectionid', 'uid', 'appname', 'hostname'])
OS_PROFILES_PERIODSQLTIMES_SEC = Gauge('os_profiles_periodsqltime_sec', 'Measured SQL Time during period', ['hostserver', 'objectserver', 'connectionid', 'uid', 'appname', 'hostname'])
OS_PROFILES_TOTALSQLTIME_SEC = Gauge('os_profiles_totalsqltime_sec', 'Total time, in seconds, for running all SQL commands for this client.', ['hostserver', 'objetcserver', 'connectionid', 'uid', 'appname', 'hostname'])
OS_PROFILES_LASTTIMINGAT_SEC = Gauge('os_profiles_lasttimingat_sec', 'Last time an SQL profile was taken for this client.', ['hostserver', 'objectserver', 'connectionid', 'uid', 'appname', 'hostname'])
OS_PROFILES_PROFILEDFROM_SEC = Gauge('os_profiles_profiledfrom_sec', 'Time at which profiling began.', ['hostserver', 'objectserver', 'connectionid', 'uid', 'appname', 'hostname'])
OS_PROFILES_NUMSUBMITS_NUM = Gauge('os_profiles_numsubmits_num', 'Number of submissions for this client.', ['hostserver', 'objectserver', 'connectionid', 'uid', 'appname', 'hostname'])
OS_PROFILES_TOTALPARSETIME_SEC = Gauge('os_profiles_totalparsetime_sec', 'Records the total amount of time spent parsing commands for this client.', ['hostserver', 'objectserver', 'connectionid', 'uid', 'appname', 'hostname'])
OS_PROFILES_RESOLVETIME_SEC = Gauge('os_profiles_totalresolvetime_sec', 'Records the total amount of time spent resolving commands for this client.', ['hostserver', 'objectserver', 'connectionid', 'uid', 'appname', 'hostname'])
OS_PROFILES_EXECTIME_SEC = Gauge('os_profiles_totalexectime_sec', 'Records the total amount of time spent running commands for this client.', ['hostserver', 'objectserver', 'connectionid', 'uid', 'appname', 'hostname'])
# OS Exportr Selfmonitoring
OSXPORTER_SELF_TOTALTHREADS_NUM = Gauge('osexporter_self_totalthreads_num', 'Active Thread objects')
OSXPORTER_SELF_OSSCRAPETIMETOTAL_SEC = Gauge('osexporter_self_osscrapetimetotal_sec', 'Time needed to scrape all data from one objectserver', ['threadname', 'hostserver', 'restport'])
OSXPORTER_SELF_OSSCRAPETIMEALERTSSTATUS_SEC = Gauge('osexporter_self_osscrapetimealertsstatus_sec', 'Time needed to scrape all alerts.status from one objectserver', ['threadname', 'hostserver', 'restport'])
OSXPORTER_SELF_OSSCRAPEHTMLRETURNCODE_NUM = Gauge('osexporter_self_osscrapehtmlreturncode_num', 'The HTML Returncode from the Objectserver Rest API', ['threadname', 'hostserver', 'restport'])
logger.info('Finished setting prometheus metric definitions')


class myOSDataThread (threading.Thread):
    def __init__(self, threadID, name, restURL, restPort, restUser, restPW):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.restURL = restURL
        self.restPort = restPort
        self.restUser = restUser
        self.restPW = restPW

    def run(self):
        logging.info("Starting Thread" + self.name)
        getOsData(self.name, self.restURL, self.restPort, self.restUser, self.restPW)
        logging.info("Exiting Thread" + self.name)

# template, replacing all hardcoded GET requests with one generic


def genericOsGet(threadName, osRest, osRestPort, osLoginUser, osLoginPW, getURL):
    response = "toBeDefinied"
    return response

# template, replacing all hardcoded POST requests with one generic


def genericOsSqlPost(threadName, osRest, osRestPort, osLoginUser, osLoginPW, SQL):
    response = session.post('http://' + osRest + osRestPort + '/objectserver/restapi/sql/factory', json={'sqlcmd': 'describe alerts.status'}, auth=(osLoginUser, osLoginPW))
    return response


def getOsData(threadName, osRest, osRestPort, osLoginUser, osLoginPW):
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
        logger.info(threadName + ': Start gathering data from ' + osRest + ' for the ' + str(requestLoopCounter) + ' time')
        startTime = time.time()
        try:
            alertsStatus = session.get('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/status?collist=Severity', auth=(osLoginUser, osLoginPW), timeout=conTimeout)
            logger.debug(threadName + ': HTML Return Code from ' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/status' + ' is: ' + str(alertsStatus.status_code))
            OSXPORTER_SELF_OSSCRAPEHTMLRETURNCODE_NUM.labels(threadName, osRest, osRestPort).set(alertsStatus.status_code)
        except:
            logger.error('Getting alert.status from ' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/status failed', exc_info=True)
        try:
            osAlertsStatus = alertsStatus.json()
            OS_EVENTS_TOTAL.labels(osRest, osAlertsStatus['rowset']['osname']).set(len(osAlertsStatus['rowset']['rows']))
            OS_COLS_TOTAL.labels(osRest, osAlertsStatus['rowset']['osname']).set(len(osAlertsStatus['rowset']['coldesc']))
            OS_NAME.info({'name': osAlertsStatus['rowset']['osname']})

            for event in osAlertsStatus['rowset']['rows']:
                if event['Severity'] == 5:
                    osEventsCritical += 1
                if event['Severity'] == 4:
                    osEventsMajor += 1
                if event['Severity'] == 3:
                    osEventsMinor += 1
                if event['Severity'] == 2:
                    osEventsWarning += 1
                if event['Severity'] == 1:
                    osEventsIndeterminate += 1
                if event['Severity'] == 0:
                    osEventsClear += 1

            OS_EVENTS_CRITICAL.labels(osRest, osAlertsStatus['rowset']['osname']).set(osEventsCritical)
            OS_EVENTS_MAJOR.labels(osRest, osAlertsStatus['rowset']['osname']).set(osEventsMajor)
            OS_EVENTS_MINOR.labels(osRest, osAlertsStatus['rowset']['osname']).set(osEventsMinor)
            OS_EVENTS_WARNING.labels(osRest, osAlertsStatus['rowset']['osname']).set(osEventsWarning)
            OS_EVENTS_INDETERMINATE.labels(osRest, osAlertsStatus['rowset']['osname']).set(osEventsIndeterminate)
            OS_EVENTS_CLEAR.labels(osRest, osAlertsStatus['rowset']['osname']).set(osEventsClear)
            alertsStatusTime = time.time() - startTime
            OSXPORTER_SELF_OSSCRAPETIMEALERTSSTATUS_SEC.labels(threadName, osRest, osRestPort).set(alertsStatusTime)
            logger.debug(threadName + ': Finished gathering data data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/status in ' + str(alertsStatusTime) + ' seconds')
        except:
            logger.error('Converting JSON into alerts.status metrics failed', exc_info=True)

        # Processing Profiles
        startProfilesTime = time.time()
        try:
            profiles = session.get('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/catalog/profiles', auth=(osLoginUser, osLoginPW), timeout=conTimeout)
        except:
            logger.error('Getting data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/catalog/profiles failed', exc_info=True)
        try:
            osProfiles = profiles.json()
            OS_PROFILES_TOTAL_NUM.labels(osRest, osProfiles['rowset']['osname']).set(osProfiles['rowset']['affectedRows'])
            for profile in osProfiles['rowset']['rows']:
                OS_PROFILES_LASTSQLTIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['ConnectionID'], profile['UID'], profile['AppName'], profile['HostName']).set(profile['LastSQLTime'])
                OS_PROFILES_MINSQLTIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['ConnectionID'], profile['UID'], profile['AppName'], profile['HostName']).set(profile['MinSQLTime'])
                OS_PROFILES_MAXSQLTIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['ConnectionID'], profile['UID'], profile['AppName'], profile['HostName']).set(profile['MaxSQLTime'])
                OS_PROFILES_PERIODSQLTIMES_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['ConnectionID'], profile['UID'], profile['AppName'], profile['HostName']).set(profile['PeriodSQLTime'])
                OS_PROFILES_TOTALSQLTIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['ConnectionID'], profile['UID'], profile['AppName'], profile['HostName']).set(profile['TotalSQLTime'])
                OS_PROFILES_LASTTIMINGAT_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['ConnectionID'], profile['UID'], profile['AppName'], profile['HostName']).set(profile['LastTimingAt'])
                OS_PROFILES_PROFILEDFROM_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['ConnectionID'], profile['UID'], profile['AppName'], profile['HostName']).set(profile['ProfiledFrom'])
                OS_PROFILES_NUMSUBMITS_NUM.labels(osRest, osProfiles['rowset']['osname'], profile['ConnectionID'], profile['UID'], profile['AppName'], profile['HostName']).set(profile['NumSubmits'])
                OS_PROFILES_TOTALPARSETIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['ConnectionID'], profile['UID'], profile['AppName'], profile['HostName']).set(profile['TotalParseTime'])
                OS_PROFILES_RESOLVETIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['UID'], profile['ConnectionID'], profile['AppName'], profile['HostName']).set(profile['TotalResolveTime'])
                OS_PROFILES_EXECTIME_SEC.labels(osRest, osProfiles['rowset']['osname'], profile['UID'], profile['ConnectionID'], profile['AppName'], profile['HostName']).set(profile['TotalExecTime'])
                profilesTime = time.time() - startTime
        except:
            logger.error('Converting converting JSON into profile metrics failed')

        # Processing Details
        try:
            alertsDetails = session.get('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/details', auth=(osLoginUser, osLoginPW), timeout=conTimeout)
        except:
            logger.error('Getting data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/details failed', exc_info=True)
        try:
            osAlertsDetails = alertsDetails.json()
            OS_ALERTS_DETAILS_TOTAL.labels(osRest, osAlertsDetails['rowset']['osname']).set(osAlertsDetails['rowset']['affectedRows'])
        except:
            logger.error('Converting converting JSON for details metrics failed')

        # Processsing Journal entrys
        try:
            alertsJournal = session.get('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/journal', auth=(osLoginUser, osLoginPW), timeout=conTimeout)
        except:
            logger.error('Getting data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/alerts/journal failed', exc_info=True)
        try:
            osAlertsJournal = alertsJournal.json()
            OS_ALERTS_JOURNAL_TOTAL.labels(osRest, osAlertsJournal['rowset']['osname']).set(osAlertsJournal['rowset']['affectedRows'])
        except:
            logger.error('Converting converting JSON into journal metrics failed')

        # Processing Connections
        try:
            connections = session.get('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/catalog/connections', auth=(osLoginUser, osLoginPW), timeout=conTimeout)
        except:
            logger.error('Getting data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/catalog/connections failed', exc_info=True)
        try:
            osConnections = connections.json()
            OS_CONNECTIONS_TOTAL.labels(osRest, osConnections['rowset']['osname']).set(osConnections['rowset']['affectedRows'])
            for connection in osConnections['rowset']['rows']:
                OS_CONNECTIONS_ISREALTIME.labels(osRest, osConnections['rowset']['osname'], connection['LogName'], connection['HostName'], connection['AppName']).set(connection['IsRealTime'])
                OS_CONNECTIONS_CONNECTTIME.labels(osRest, osConnections['rowset']['osname'], connection['LogName'], connection['HostName'], connection['AppName']).set(connection['ConnectTime'])
        except:
            logger.error('Converting converting JSON into connection metrics failed')

        # Processing Memstore
        try:
            memstores = session.get('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/catalog/memstores', auth=(osLoginUser, osLoginPW), timeout=conTimeout)
        except:
            logger.error('Getting data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/catalog/memstores failed', exc_info=True)
        try:
            osMemstores = memstores.json()
            for memstore in osMemstores['rowset']['rows']:
                OS_MEMSTORE_HARDLIMIT_BYTES.labels(osRest, osMemstores['rowset']['osname'], memstore['StoreName'], memstore['IsProtected']).set(memstore['HardLimit'])
                OS_MEMSTORE_SOFTLIMIT_BYTES.labels(osRest, osMemstores['rowset']['osname'], memstore['StoreName'], memstore['IsProtected']).set(memstore['SoftLimit'])
                OS_MEMSTORE_USEDBYTES_BYTES.labels(osRest, osMemstores['rowset']['osname'], memstore['StoreName'], memstore['IsProtected']).set(memstore['UsedBytes'])
        except:
            logger.error('Converting converting JSON into memstore metrics failed')

        # Trigger Processing
        osTriggerActiveCount = 0
        osTriggerInactiveCount = 0

        try:
            triggerStats = session.get('http://' + osRest + ':' + osRestPort + '/objectserver/restapi/catalog/trigger_stats', auth=(osLoginUser, osLoginPW), timeout=conTimeout)
        except:
            logger.error('Getting data from ' + osRest + ':' + osRestPort + '/objectserver/restapi/catalog/trigger_stats failed', exc_info=True)
        try:
            osTriggerStats = triggerStats.json()
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
        totalTime = time.time() - startTime
        OSXPORTER_SELF_OSSCRAPETIMETOTAL_SEC.labels(threadName, osRest, osRestPort).set(totalTime)
        logger.info(threadName + ': Finished gathering data data from ' + osRest + ':' + osRestPort + ' for the ' + str(requestLoopCounter) + ' time in ' + str(totalTime) + ' seconds')
        requestLoopCounter = requestLoopCounter + 1
        if exitFlag:
            threadName.exit()
        time.sleep(osReqFreq)


if __name__ == '__main__':
    # Reading Config File
    logger.info('Reading initial config from os_exporter_cfg.yaml')
    try:
        with open("os_exporter_cfg.yaml", 'r') as ymlfile:
            exportercfg = yaml.load(ymlfile)
    except:
        logger.error('Error Reading configfile')

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
    for objectserver in exportercfg['objectservers']:
        oscounter = oscounter + 1
        threadname = 'thread' + str(oscounter)
        thread = myOSDataThread(oscounter, threadname, str(objectserver['address']), str(objectserver['port']), str(objectserver['user']), str(objectserver['pw']))
        thread.start()

    logger.info('Threads started')
    logger.info('Active Thread objects: ' + str(threading.activeCount()))
    logger.info('Thread objects in callers thread control: ' + str(threading.currentThread()))
    logger.info('Starting Main Loop')

    # main loop
    while True:
        threadActiveCounts = threading.activeCount()
        OSXPORTER_SELF_TOTALTHREADS_NUM.set(threadActiveCounts)
        logger.debug('Active Thread objects: ' + str(threadActiveCounts))
        logger.debug('Thread objects in callers thread control: ' + str(threading.enumerate()))
        time.sleep(30)
