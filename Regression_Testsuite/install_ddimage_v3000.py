#/usr/bin/python
#Author: Patrick Shapard @HPE,
#created: 04/22/2021
#updated: 06/14/2021
#The script retrieves the latest TOT DD image for the latest release.  Then connects to the CIM and installs DD image and
#waits for 120mins to download and install new image.  Then it waits an additional 30mins to complete.
#The set_https_proxies is used to connect to the DD image repository in Ft Collins, CO.


import sys
import logging
import socket
import urllib2
from HTMLParser import HTMLParser

from SynergyV3000 import api, username, ov_pw, user, cim_pw
from SynergyV3000 import LoginCreds
from SynergyV3000 import OneViewBuildVersion
from SynergyV3000 import Enclosures
from SynergyV3000 import printDict #function
from SynergyV3000 import countdown #function
from SynergyV3000 import sshclient
from SynergyV3000 import InstallNewSynergyImages
from SynergyV3000 import clear_https_proxies
from SynergyV3000 import setup_logging_Enhanced
from SynergyV3000 import get_eagle_enclosure_map
from SynergyV3000 import get_ip_from_command_line
from requests.exceptions import ConnectionError

filename = 'install_ddimage_v3000'
links = []
pass_build = []
InstallImage = InstallNewSynergyImages()
#The InstallNewDDImage function has a timer of 60mins, and another 90mins, total of 2hrs 30mins


def get_auth_token(ip):
    login_inst = LoginCreds()
    try:
        auth = login_inst.LoginToken(ip, api, username, ov_pw)
    except ConnectionError as e:
        logging.info("Could not connect to host")
        # logging.info("{}" .format(e))
        sys.exit(0)
    return auth


def GetComposerType(ip, auth):
    logging.info("Checking for Composer Type")
    enc_inst = Enclosures()
    EncDict = enc_inst.GetEnc(ip,auth,api)
    enc_list = printDict(EncDict, ['name', 'version', 'state'])
    flm_mgr_bays = printDict(EncDict, ['managerBays'])
    cim_mgr_list = printDict(EncDict, ['applianceBays'])
    for i, value in enumerate(enc_list):
        cim_bays = cim_mgr_list[i]['applianceBays']
        for k, value in enumerate(cim_bays):
            cim_presence = cim_bays[k]['devicePresence']
            cim_model = cim_bays[k]['model']
            if cim_presence == "Present":
                logging.info("Composer Type: {}" .format(cim_model))
                if cim_model == "Synergy Composer":
                    return 'Composer-SSH'
                elif cim_model == "Synergy Composer2":
                    return 'Composer2-SSH'
            else:
                pass



def get_type_of_oneview_build():
    get_type_of_oneview_build_dict = {
        'top': 'ToT',
        'pass': 'PassBuild',
    }

    prompt = "What type of OneView build? For ToT, type 'top', for passbuild, choose 'pass' {}: ".format(get_type_of_oneview_build_dict.keys())
    response = raw_input(prompt).lower()

    if response in get_type_of_oneview_build_dict:
        build = get_type_of_oneview_build_dict[response]
    else:
        print "You need to specify a OneView build, please try again "
        sys.exit(0)

    print("You have chosen {} \n"  .format(response))
    return build


def get_oneview_build_release():
    get_build_release_dict = {
        '5.10': 'rel/5.10',
        '5.20': 'rel/5.20',
        '5.30': 'rel/5.30',
        '5.40': 'rel/5.40',
        '5.50': 'rel/5.50',
        '5.60': 'rel/5.60',
        '6.00': 'rel/6.00',
        '6.10': 'rel/6.10',
        '6.20': 'rel/6.20',
        'latest': 'master'
    }

    prompt = "Which OneView release?  {}: ".format(get_build_release_dict.keys())
    response = raw_input(prompt).lower()

    if response in get_build_release_dict:
        rel_build = get_build_release_dict[response]
    else:
        print "You need to specify a OneView release build, please try again "
        sys.exit(0)

    print("You have chosen release {} \n"  .format(response))
    return rel_build




class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        attr = dict(attrs)
        links.append(attr)
 
def get_ddimage_links(dd_image_url):
    url = "{}" .format(dd_image_url)
    try:
        f = urllib2.urlopen(url)
        html = f.read()
        f.close()
    except urllib2.HTTPError as e:
        print(e, 'while fetching', url)
        return
 
    parser = MyHTMLParser()
    parser.links = []
    parser.feed(html)
    for l in links:
        pass
    return links


def retrieve_ToT_DDimages_impl(ddimage_links):
    ddimage_links_sorted = sorted(ddimage_links)
    last_element = ddimage_links_sorted[-3]
    last_element1 = str(last_element)
    init_tot_image = last_element1[10:66]
    tot_build_temp = init_tot_image.translate(None, "'}")
    tot_image = tot_build_temp.strip()
    return tot_image
    
def retrieve_Pass_DDimages_impl(ddimage_links):
    ddimage_links_sorted = sorted(ddimage_links)
    for d, value in enumerate(ddimage_links_sorted):
        image_List = ddimage_links_sorted[d]
        image_List_str = str(image_List)
        IndexName = image_List_str[51:55]
        if IndexName == "PASS":
            pass_build.append(image_List_str)
        IndexName = image_List_str[50:54]
        if IndexName == "PASS":
            pass_build.append(image_List_str)
    try:
        last_pass_build = pass_build[-2]
    except IndexError as e:
        print("could not retrieve any pass build images")
        sys.exit(0)
    last_pass_build_list = str(last_pass_build)
    init_pass_image = last_pass_build_list[10:66]
    pass_build_temp = init_pass_image.translate(None, "'}")
    pass_image = pass_build_temp.strip()
    return pass_image


def copy_shell_script_to_cim(ip):
    logging.info("Connecting to CIM, uploading shell script to start the DD image install process.")
    CopyCanmicME(ip, user, cim_pw)
    logging.info("setting permissions to shell script")
    cmd = 'chmod 777 *'
    sshclient(ip, user, cim_pw, cmd)
    countdown(0, 5)


def main():
    ip = get_ip_from_command_line()
    eagle = get_eagle_enclosure_map(ip)
    setup_logging_Enhanced(eagle, filename)
    auth = get_auth_token(ip)
    composer_ver = GetComposerType(ip, auth)
    build = get_type_of_oneview_build()
    build_release = get_oneview_build_release()
    dd_image_url = "http://ci-artifacts04.vse.rdlabs.hpecorp.net/omni/%s/DDImage/%s/" %(build_release, composer_ver)
    ddimage_links = get_ddimage_links(dd_image_url)
    if build == 'ToT':
        tot_image = retrieve_ToT_DDimages_impl(ddimage_links)
        logging.info("The length of the tot build is:  {}" .format(len(tot_image)))
        logging.info("The tot image being installed: {}" .format(tot_image))
        InstallImage.InstallNewDDImageNew(ip, user, cim_pw, dd_image_url, tot_image)
    elif build == 'PassBuild':
        pass_image = retrieve_Pass_DDimages_impl(ddimage_links)
        logging.info("The length of the pass build is:  {}" .format(len(pass_image)))
        logging.info("The pass build image being installed: {}" .format(pass_image))
        InstallImage.InstallNewDDImageNew(ip, user, cim_pw, dd_image_url, pass_image)
    clear_https_proxies()
    countdown(30, 0)

if __name__ == '__main__':
    main()
