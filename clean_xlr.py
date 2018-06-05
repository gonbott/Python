import base64
import json
import urllib.request
import configparser
import logging
import logging.config
from datetime import datetime, timedelta

# Constants
DATE_LIMIT = 0
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
FILTER_STATUS = ['TEMPLATE', 'ABORTED', 'COMPLETED']
REPORT_FILE_NAME_TEMPLATE = 'filtered_releases_#.csv'
XLR_API_USER = 'xlrelease'
XLR_API_PASSWORD = 'AhThie7e'
XLR_API_GET_RELEASES = 'https://release.lstools.int.clarivate.com/api/v1/releases/'
ABORT = 'https://release.lstools.int.clarivate.com/api/v1/releases/#/abort'
# Constants
CONFIG_FILE = 'xlr_cleanup.conf'

# Set up logger
logging.config.fileConfig(CONFIG_FILE, disable_existing_loggers=False)
logger = logging.getLogger('xlr_cleanup')
logger.info('Cleanup process started')

# Read configuration
logger.debug('Using configuration file [{}]'.format(CONFIG_FILE))
config = configparser.RawConfigParser()
config.read(CONFIG_FILE)

# Calculate limit day
limitDate = datetime.today() - timedelta(days=DATE_LIMIT)

# Generate HTTP basic auth
#base64auth = base64.b64encode('{}:{}'.format(XLR_API_USER, XLR_API_PASSWORD).encode())
#authHeader = 'Basic {}'.format(base64.b64encode(base64auth).decode())
authHeader = "Basic {}".format(base64.b64encode("{}:{}".format(XLR_API_USER, XLR_API_PASSWORD).encode()).decode())

# Get all releases
# For debug: jsonReleases = open('file.json')
httpRequest = urllib.request.Request(XLR_API_GET_RELEASES)
httpRequest.add_header("Authorization", authHeader)
jsonReleases = urllib.request.urlopen(httpRequest)
allReleases = json.load(jsonReleases)

# Filter templates, aborted and completed releases
counter = {}
filteredReleases = []
for release in allReleases:
     if release['status'] not in FILTER_STATUS:
         modifyDate = datetime.strptime(
             release['$lastModifiedAt'][:-5], DATE_FORMAT)
         if limitDate > modifyDate:
             temp = {}
             temp.update({'status': str(release['status'])})
             temp.update({'id': str(release['id']).replace('/', '-')})
             temp.update({'queryableStartDate': str(release['queryableStartDate'])})
             temp.update({'lastModifiedAt': str(release['$lastModifiedAt'])})
             temp.update({'title': str(release['title'])})
             temp.update({'owner': str(release['owner'])})
             temp.update({'tags': str(release['tags'])})
             if 'originTemplateId' in release.keys():
                 temp.update({'originTemplateId': release['originTemplateId']})
             else:
                 temp.update({'originTemplateId': ''})
             filteredReleases.append(temp)

# # Generate release report
# print ('Releases found: {}'.format(len(allReleases)))
# print ('Filtered releases: {}'.format(len(filteredReleases)))
# print ('Filters:')
# print (' - Release status not in {}'. format(FILTER_STATUS))
# print (' - Release lastModifiedAt before than {}'.format(limitDate.date()))

for release2 in filteredReleases:
     #print (release2['title'])
     if 'Applications-Folder754780610-Folder480752997-Release287976146' in str(release2['id']):
         try:
             RAM = ABORT.replace('#', str(release2['id']).replace('-', '/'))
             _httpRequest = urllib.request.Request(RAM)
             _httpRequest.add_header("Authorization", authHeader)
             logger.debug('Aborting release [{}]'.format(_httpRequest.get_full_url()))
             _jsonReleases = urllib.request.urlopen(_httpRequest)
             #_counter += 1
         except (urllib.error.HTTPError, urllib.error.URLError) as error:
             logger.error('Release abort failed! [{}]'.format(release2['id']))
             logger.debug('Exception caught [{}]'.format(error))
             #print ('Error')

             