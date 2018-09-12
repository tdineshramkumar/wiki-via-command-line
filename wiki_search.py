"""
T Dinesh Ram Kumar
Shows extracts from Wiki using Wikipedia API
Based on:
1.  https://www.mediawiki.org/wiki/User:SSethi_(WMF)/Sandbox/API:Opensearch
2.  https://en.wikipedia.org/api/rest_v1/#!/Page_content/get_page_summary_title
Needs wiki2text if command line support needed
"""

import requests
import sys
from getopt import GetoptError, getopt
from os.path import basename, exists
from os import system
from subprocess import Popen, PIPE
# comment the selenium usage if browser support not needed 
# from selenium import webdriver
from urllib.parse import urlparse, unquote

# Refer to Wikipedia API page for explanations
DEFAULT_LIMIT = 10
DEFAULT_NAMESPACE = 0
URL = "https://en.wikipedia.org/w/api.php"
SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}?redirect=true"
WIKI_PAGE_URL = "https://en.wikipedia.org/api/rest_v1/page/html/{}"
WIKI_TEXT_COMMAND = 'html2text -utf8 -style pretty -width `tput cols`'
SHOW_IN_BROWSER = False
WIKI_TEXT = False
DETAILED = False
PARSABLE = False
SHELL = "/bin/bash"


def usage():
    print("Usage: {} [OPTION...] command".format(basename(sys.argv[0])))
    print("Searches and gets extracts from the wiki using Wikipedia API in OpenSearch Format.")
    print("Options:")
    print("\t--help, -h\n\t\tGive the usage.")
    # print("\t--browser, -b\n\t\tOpen in browser.")
    print("\t--parse, -p\n\t\tPrint in parse-able format (OpenSearch Format).")
    print("\t--detail, -d\n\t\tFetch and display a more detailed Extract.")
    print("\t--limit, -l\n\t\tSet the limit. Default limit = {!s}".format(DEFAULT_LIMIT))
    print("\t--namespace, -n\n\t\tSet the wikipedia namespace. Default namespace = {!s}".format(DEFAULT_NAMESPACE))
    print("\t--text, -t\n\t\tShow wikipedia page in command line using wiki2text")


try:
    # SHORT_OPTIONS = "hdl:n:bpt"
    # LONG_OPTIONS = ["help", "detail", "limit=", "namespace=", "browser", "parse", "text"]
    SHORT_OPTIONS = "hdl:n:pt"
    LONG_OPTIONS = ["help", "detail", "limit=", "namespace=", "parse", "text"]
    opts, argv = getopt(args=sys.argv[1:], shortopts=SHORT_OPTIONS, longopts=LONG_OPTIONS)
    SEARCH_TERM = " ".join(argv).strip()
    if SEARCH_TERM == '':
        print("Specify the search term.")
        usage()
        sys.exit()
except GetoptError as error:    # if invalid options then print error, usage and then exit
    print(error)
    usage()
    sys.exit(-1)

for o, a in opts:
    if o in ("-h", "--help"):   # used to show usage
        usage()
        sys.exit(0)
    if o in ("--browser", "-b"):
        SHOW_IN_BROWSER = True
    if o in ("--parse", "-p"):
        PARSABLE = True
    if o in ("--detail", "-d"):
        DETAILED = True
    if o in ("--limit", "-l"):
        DEFAULT_LIMIT = int(a)
    if o in ("--namespace", "-n"):
        DEFAULT_NAMESPACE = int(a)
    if o in ("--text", "-t"):
        WIKI_TEXT = True

PARAMS = {
    'action': "opensearch",
    'search': SEARCH_TERM,
    'limit': DEFAULT_LIMIT,
    'namespace': DEFAULT_NAMESPACE,
    'format': "json"
}

detailed_wiki = lambda title: requests.get(SUMMARY_URL.format(title)).json()['extract']

R = requests.get(url=URL, params=PARAMS)    # Send the GET request with desired parameters
DATA = R.json()                             # convert it to JSON (OpenSearch Specifications)

if PARSABLE and DETAILED:   # If print in detailed and parsable manner
    for index, title in enumerate(DATA[1]):
        DATA[2][index] = detailed_wiki(title)
    print(DATA)
elif PARSABLE:  # if only parsable manner
    print(DATA)
else:
    # Print the contents
    if DATA[1]:     # if some search results then ..
        for index, (title, data, url) in enumerate(zip(DATA[1], DATA[2], DATA[3]), 1):
            if DETAILED:
                data = detailed_wiki(title)
            print("{0!s}. \033[031;1m{1}\033[0m:\t[{2}]\n\t\033[1m{3}\033[0m\n".format(index, title, unquote(url), data))

        if WIKI_TEXT:
            index = int(input("Enter index [{}-{}]:".format(1, len(DATA[1]))))
            index = max(min(len(DATA[1]), index), 1) - 1
            title = basename(urlparse(DATA[3][index]).path)
            with Popen([SHELL, "-c", WIKI_TEXT_COMMAND], stdin=PIPE, stdout=PIPE) as pipe:  # Both in, out via pipe
                R = requests.get(WIKI_PAGE_URL.format(title))
                stdout, stderr = pipe.communicate(R.text.encode('utf-8'))
                print(stdout.decode(errors='ignore'))
        elif SHOW_IN_BROWSER:
            print("Browser View: ")
            index = int(input("Enter index [{}-{}]:".format(1, len(DATA[1]))))
            index = max(min(len(DATA[1]), index), 1) - 1
            driver = webdriver.Firefox()
            driver.get(DATA[3][index])
    else:
        print("No Results found for {}.".format(DATA[0]))

