#/usr/bin/python
#Author: Patrick Shapard @HPE,
#created: 1/05/2022
#updated: 1/05/2022
#The script retrieves the latest TOT DD image for the latest release.  Then connects to the CIM and installs DD image and
#waits for 120mins to download and install new image.  Then it waits an additional 30mins to complete.
#The second part of the script configures eagle28 and ensures its ready for the regression test run
#The third part executes the regression test suite.

"""
TestCase: Carbon Failover stress test(multiple iterations)
TestCase: Carbon Efuse stress test with power off
TestCase: Restart of Oneview (multiple iterations)
TestCase: Carbon Reset stress test
TestCase: Remove/Add FC Network from ULS from LIG (multiple iterations)
TestCase: Remove/Add FC Network from ULS from LI (multiple iterations)
TestCase: UFG LE with A-Side B-side LIGs
TestCase: Enable/Disable RemoteSyslog Ipv4 and Ipv6
TestCase: Efuse Carbon Stress Test (multiple iterations)
TestCase: Add/Remove IPv4 Static Address Range to/from Enclosure Group
TestCase: Remove/Add LIG from/to Enclosure Group
TestCase: Change port speeds(4/8/16GB) on ToR FC switch
TestCase: Connector Information and Digital Diagnostics
TestCase: Disable/Enable Trunking on LIG
TestCase: Server Profile FC Connection set to 16GB/Auto
TestCase: Carbon Utilization Samples
TestCase: Update/Reset carbon hostname
TestCase: Carbon Neighbor switch WWN
TestCase: Oneview LE Supportdump(encrypted)
TestCase: Appliance Backup/Restore
"""
import logging
import subprocess
import sys

import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from requests.exceptions import ConnectionError

from SynergyV3800 import InstallNewSynergyImages
from SynergyV3800 import AddRemoveUplinkSetsLiME
from SynergyV3800 import ApplianceBackup
from SynergyV3800 import ApplianceSettings
from SynergyV3800 import CheckAllStatesOfCarbon
from SynergyV3800 import CheckStateOfCarbon
from SynergyV3800 import ConfigureTOR
from SynergyV3800 import ConnectorDigDiagInfo
from SynergyV3800 import CreateEnclosureGroupME
from SynergyV3800 import CreateFibreChannelNetworks
from SynergyV3800 import CreateLogicalEnclosureME
from SynergyV3800 import CreateLogicalInterconnectGroupME
from SynergyV3800 import EfuseResource
from SynergyV3800 import Enclosures
from SynergyV3800 import GetCarbonAddressType
from SynergyV3800 import GetCarbonDownLinkPorts
from SynergyV3800 import GetCarbonPortStatus
from SynergyV3800 import GetCarbonUpLinkPorts  # function
from SynergyV3800 import GetFLOGI
from SynergyV3800 import GetSPStatus
from SynergyV3800 import GetStatusOfLogicalEnclosure
from SynergyV3800 import Interconnects
from SynergyV3800 import LogicalEnclosure
from SynergyV3800 import LogicalInterconnectGroup
from SynergyV3800 import LogicalInterconnects
from SynergyV3800 import LoginCreds
from SynergyV3800 import Networks
from SynergyV3800 import OneViewBuildVersion
from SynergyV3800 import PassOrFail  # function
from SynergyV3800 import PowerOffOnServers
from SynergyV3800 import PowerStateOfCarbon
from SynergyV3800 import RemoteSyslog
from SynergyV3800 import ServerProfileBfsLunsNewDTO
from SynergyV3800 import ServerProfileConnectionSpeeds
from SynergyV3800 import Servers
from SynergyV3800 import StateOfEnclosure
from SynergyV3800 import UpdateEnclosureGroupME
from SynergyV3800 import UpdateLogicalEnclosure
from SynergyV3800 import UpdateLogicalInterconnectGroupME
from SynergyV3800 import UpdateLogicalInterconnects
from SynergyV3800 import UpdateServerProfileBfsLunsNewDTO
from SynergyV3800 import api, username, user, ov_pw, tor_pw, tor_un, old_pw
from SynergyV3800 import countdown  # function
from SynergyV3800 import determine_num_iterations  # function
from SynergyV3800 import get_eagle_enclosure_map
from SynergyV3800 import get_tor_ip
from SynergyV3800 import printDict  # function
from SynergyV3800 import setup_logging_Enhanced
from SynergyV3800 import untar_supportdump  # function
from SynergyV3800 import get_ov_build_version
from SynergyV3800 import oneview_upgrade_check
from SynergyV3800 import get_filename
from SynergyV3800 import set_https_proxies_houston
from SynergyV3800 import clear_https_proxies




# Global variables
ip = "15.186.9.28"
filename = 'TotalTestSuitePackageV3800'
docker_ip = '15.186.21.30'
docker_pw = 'hponeview'
yaml_file = 'e28'
links = []
pass_build = []
InstallImage = InstallNewSynergyImages()
fc_mode = "TRUNK"
v3_enabled = "true"
consistency_check = "ExactMatch"
enc_one = 'CN7516060B'
enc_two = 'CN75150100'
enc1_uri = '/rest/enclosures/000000CN7516060B'
enc2_uri = '/rest/enclosures/000000CN75150100'
icm_name_rdl = 'CN7516060B, interconnect 1'
build = "ToT"
build_release = "main"
number = 0


def get_auth_token():
    login_inst = LoginCreds()
    try:
        auth = login_inst.LoginToken(ip, api, username, ov_pw)
    except ConnectionError as e:
        logging.info("Could not connect to host")
        logging.info("{}" .format(e))
        sys.exit(0)
    return auth


def get_new_auth_token():
    login_inst = LoginCreds()
    try:
        login_inst.AcceptEULA(ip, api)
        login_inst.InitialLogin(ip, api, ov_pw, old_pw)
        auth = login_inst.LoginToken(ip, api, username, ov_pw)
        return auth
    except ConnectionError as e:
        logging.info("Could not connect to host")
        logging.info("{}".format(e))
        sys.exit(0)



def GetComposerType(auth):
    logging.info("Checking for Composer Type")
    enc_inst = Enclosures()
    EncDict = enc_inst.GetEnc(ip,auth,api)
    enc_list = printDict(EncDict, ['name', 'version', 'state'])
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

    prompt = "What type of OneView build? For ToT, type 'top', for passbuild, choose 'pass' {}: ".format(list(get_type_of_oneview_build_dict.keys()))
    response = input(prompt).lower()

    if response in get_type_of_oneview_build_dict:
        build = get_type_of_oneview_build_dict[response]
    else:
        print("You need to specify a OneView build, please try again ")
        sys.exit(0)

    print("You have chosen {} \n"  .format(response))
    return build


def get_oneview_build_release():
    get_build_release_dict = {
        '6.00': 'rel/6.00',
        '6.10': 'rel/6.10',
        '6.20': 'rel/6.20',
        '6.30': 'rel/6.30',
        '6.40': 'rel/6.40',
        'latest': 'main'
    }

    prompt = "Which OneView release?  {}: ".format(list(get_build_release_dict.keys()))
    response = input(prompt).lower()

    if response in get_build_release_dict:
        rel_build = get_build_release_dict[response]
    else:
        print("You need to specify a OneView release build, please try again ")
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
        f = urllib.request.urlopen(url)
        html = str(f.read())
        f.close()
    except urllib.error.HTTPError as e:
        print(e, 'while fetching', url)
        return
 
    parser = MyHTMLParser()
    parser.links = []
    parser.feed(html)
    for l in links:
        pass
    return links

def retrieve_ToT_DDimages_impl(ddimage_links):
    ddimage_links_sorted = list(ddimage_links)
    last_element = ddimage_links_sorted[-3]
    last_element1 = str(last_element)
    init_tot_image = last_element1[10:66]
    tot_build_temp = init_tot_image.translate({ord(i): None for i in "'}"})
    tot_image = tot_build_temp.strip()
    return tot_image

def retrieve_Pass_DDimages_impl(ddimage_links):
    ddimage_links_sorted = list(ddimage_links)
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
    pass_build_temp = init_pass_image.translate({ord(i): None for i in "'}"})
    pass_image = pass_build_temp.strip()
    return pass_image

###################################################################################################################################################
"""
This section of code configures Eagle28 with FC networks, LIGs, EG, LE and 6 Server Profiles
"""
###################################################################################################################################################

def get_ov_build_carbon_fw_version(auth, enc_name):
    get_build_inst = OneViewBuildVersion()
    ic_fw_inst = Interconnects()
    carbon_fw = ic_fw_inst.getCarbonFwVersion(ip, auth, api, enc_name)
    version = get_build_inst.GetOVBuild(ip, auth, api)
    num_iter = determine_num_iterations(number)
    logging.testcases("The OneView version/build is: {}".format(version))
    logging.testcases("The ip address of this enclosure is: {}".format(ip))
    logging.testcases("The carbon fw version is: {}".format(carbon_fw))
    logging.testcases("The number of iterations for this test run is: {}".format(num_iter))


def create_fc_networks(auth):
    fibre_chanel_network = ('BAY1_ENC1', 'BAY1-Q3-PORTS-ENC1', 'BAY4_ENC1', 'BAY1_ENC2', 'BAY4_ENC2')
    for net in fibre_chanel_network:
        logging.info("Creating {} network".format(net))
        fc_networks_inst = CreateFibreChannelNetworks()
        fc_networks_inst.CreateFcNetwork(ip, auth, api, net)


def interconnect_type_uri(auth):
    logging.info("Getting interconnect types uri")
    ic_inst = Interconnects()
    ic_types = ic_inst.GetInterconnectTypes(ip, auth, api)
    ic_types_name_uri = printDict(ic_types, ['name', 'uri'])
    return ic_types_name_uri


def get_enclosure_name(auth):
    logging.info("Getting Enclosures ")
    enc_inst = Enclosures()
    enc_dict = enc_inst.GetEnc(ip, auth, api)
    enc_name = printDict(enc_dict, ['name'])
    return enc_name


def create_carbon_lig(auth, ic_types_name_uri):
    logging.info("Entering into LIG Loop")
    retrieve_net_inst = Networks()
    create_lig_inst = CreateLogicalInterconnectGroupME()
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc2_bay1uri, fc_net_enc2_bay4uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle28(
        ip, auth, api)
    lig_name_list = ('LIG1', 'LIG2')
    for s, value in enumerate(ic_types_name_uri):
        ic_uri = ic_types_name_uri[s]['uri']
        ic_name = ic_types_name_uri[s]['name']
        if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
            for i, value in enumerate(lig_name_list):
                lig_name = lig_name_list[i]
                if lig_name == "LIG2":
                    create_lig_inst.CreateLig1E28(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay1uri,
                                                  fc_net_enc2_bay4uri, fc_mode, v3_enabled, consistency_check)
                elif lig_name == "LIG1":
                    create_lig_inst.CreateLigE28(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay1_uri,
                                                 fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, fc_mode, v3_enabled,
                                                 consistency_check)

    logging.info("Pausing for 30 secs for LIGs to be created\n")
    countdown(30)


def get_lig_uri(auth):
    logging.info("*******************CREATING EG ***************************")
    logging.info("Getting list of LIGs")
    ligs_inst = LogicalInterconnectGroup()
    list_of_lig = ligs_inst.GetListOfLIGs(ip, auth, api)
    lig_names = printDict(list_of_lig, ['name'])
    lig_uri = printDict(list_of_lig, ['uri'])
    for i, value in enumerate(lig_names):
        lig_name = lig_names[i]['name']
        if lig_name == "LIG1":
            lig1_uri = lig_uri[i]['uri']
        elif lig_name == "LIG2":
            lig2_uri = lig_uri[i]['uri']
    return lig1_uri, lig2_uri


def create_enclosure_group(auth, lig1_uri, lig2_uri):
    create_eg_inst = CreateEnclosureGroupME()
    create_eg_inst.CreateEgE28(ip, auth, api, lig1_uri, lig2_uri)
    logging.info("Pausing for 30 secs for EG to be created")
    countdown(30)


def get_enclosure_enc_group_uri(auth):
    logging.info("Getting Enclosure and Enclosure Group ")
    enc_inst = Enclosures()
    enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
    enclosure_group_uri = printDict(enc_grp_dict, ['uri'])
    enc_grp_uri = enclosure_group_uri[0]['uri']
    return enc_grp_uri


def create_le(auth, enc_grp_uri):
    logging.info("Creating Logical Enclosure")
    create_le_inst = CreateLogicalEnclosureME()
    create_le_inst.CreateLeE28(ip, auth, api, enc1_uri, enc2_uri, enc_grp_uri)
    logging.info("Pausing for 10mins.  Waiting for LE to be created")
    countdown(600)


def check_le_status(auth):
    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)


def create_server_profiles(auth, eagle, enc_grp_uri):
    retrieve_net_inst = Networks()
    power_cycle_server_inst = PowerOffOnServers()
    server_hw_profile_inst = Servers()
    create_sp_inst = ServerProfileBfsLunsNewDTO()
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc2_bay1uri, fc_net_enc2_bay4uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle28(
        ip, auth, api)
    logging.info("Getting Server HW and Profiles")
    array_wwpn1, array_wwpn2, wwnn1_start, wwpn1_start, wwnn2_start, wwpn2_start = server_hw_profile_inst.server_wwnn_start_wwpn_start(
        eagle)
    sp_name, sp_descr, id_1, id_2 = server_hw_profile_inst.server_profile_config()
    wwnn1, wwpn1, wwnn2, wwpn2 = server_hw_profile_inst.server_wwwn_wwpn(wwnn1_start, wwpn1_start, wwnn2_start,
                                                                         wwpn2_start)
    server_hw_list = server_hw_profile_inst.ServerHW(ip, auth, api)
    server_hw_names_dict = printDict(server_hw_list, ['name', 'uri', 'model', 'serialNumber'])
    power_cycle_server_inst.power_off_servers(ip, auth, api)
    mode = "UEFI"
    logging.info("starting Server HW list loop to create server profiles")
    for i, value in enumerate(server_hw_names_dict):
        server_hw_uri = server_hw_names_dict[i]['uri']
        server_name = server_hw_names_dict[i]['name']
        server_sn = server_hw_names_dict[i]['serialNumber']
        logging.info("Creating {} for server {} with SN {}".format(sp_name[i], server_name, server_sn))
        if server_sn == "MXQ915012C" or server_sn == "MXQ94701Y5" or server_sn == "MXQ94701Y4":
            create_sp_inst.CreateServerProfileLuns(ip, auth, api, sp_name[i], server_hw_uri, enc_grp_uri, sp_descr[i],
                                                   fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, id_1[i], id_2[i],
                                                   wwnn1[i], wwpn1[i], wwnn2[i], wwpn2[i], mode)
        elif server_sn == "MXQ94701Y9" or server_sn == "MXQ94701Y7" or server_sn == 'MXQ94701YC':
            create_sp_inst.CreateServerProfileLunsEnc2(ip, auth, api, sp_name[i], server_hw_uri, enc_grp_uri,
                                                       sp_descr[i], fc_net_enc2_bay1uri, fc_net_enc2_bay4uri, id_1[i],
                                                       id_2[i], wwnn1[i], wwpn1[i], wwnn2[i], wwpn2[i], mode)
        else:
            pass
    logging.info("*******************POWERING ON SERVERS **********************************")
    logging.info("Pausing 7m30s for server profiles to be created before powering on the servers")
    countdown(480)


def check_sp_status(auth):
    tc = "Create Server Profiles"
    logging.info("Checking status of server profiles")
    sp_status = GetSPStatus(ip, auth, api)
    if sp_status == "Normal":
        result = "Pass"
    else:
        result = "Fail"
        sys.exit(0)
    PassOrFail(result, tc)
    power_cycle_server_inst = PowerOffOnServers()
    power_cycle_server_inst.power_on_servers(ip, auth, api)
    countdown(600)
    power_cycle_server_inst.check_server_power(ip, auth, api)


def preflight_check(auth, tor_ip, enc_name):
    logging.info("Checking state of carbons before starting testsuite")
    check_carbon_inst = CheckStateOfCarbon()
    check_carbon_inst.CheckCarbonForErrors(ip, auth, api, enc_name)
    check_carbon_inst.CheckCarbonState(ip, auth, api, enc_name)
    get_num_flogi_inst = GetFLOGI()
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)


##################################REGRESSION TESTSUITE STARTS HERE####################################################################################

def testcase_power_off_on_carbon(auth, tor_ip, enc_name):
    """
    1) power off carbon in bay1
    2) wait 2mins
    3) check if carbon is powered off
    4) wait another 5 mins
    5) power on
    6) wait 7 mins
    7) check if carbon is configured state, if ok, 
    8( move on to the next carbon in bay4 and repeat above steps.
    """
    # This test case powers off carbon in bay4, waits 10 mins, powers on carbon, then powers off carbon in bay1.
    logging.testcases("#####################################")
    logging.testcases("TestCase: Carbon Failover stress test")
    logging.testcases("#####################################")

    testcase = 'Carbon Failover stress test'
    # number = 5  Use this variable only when you want to run this TC for less iterations than the test suite.
    counter = 0
    logging.info("Checking the status of the downlink and uplink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    all_states_inst = CheckAllStatesOfCarbon()
    check_carbon_inst = CheckStateOfCarbon()
    get_num_flogi_inst = GetFLOGI()

    countdown(5)

    #While loop to turn off and on carbon ICMs
    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Getting Interconnects")
        ic_inst = Interconnects()
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnectMultiEnc(ip, auth, api, name)
            ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])
            # For loop to interate thru carbon in bay4 and power it off
            logging.info("Power off the carbon ICMs in bay4")
            for ic, value in enumerate(ic_name_uri_list):
                ic_uri = ic_name_uri_list[ic]['uri']
                ic_name = ic_name_uri_list[ic]['name']
                name = ic_name_uri_list[ic]['enclosureName']
                carbon_power_inst = PowerStateOfCarbon()
                if ic_name == "{}, interconnect 4".format(name):
                    logging.info("Powering off the carbon in {}".format(ic_name))
                    carbon_power_inst.PowerOffCarbon(ip, auth, api, ic_uri)
                else:
                    pass
    
        countdown(120)
        logging.info("Checking to see if carbons are actually turned off")
        tc = "Power turned off on carbon bay4"
        check_carbon_inst.IsCarbonTurnedOffBay4(ip, auth, api, enc_name)
        result = "Pass"
        PassOrFail(result, tc)
        logging.info("Waiting 3 minutes before powering on carbons in bay4.")
        countdown(180)
    
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnectMultiEnc(ip, auth, api, name)
            ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])
            # For loop to interate thru carbon ICM in Bay4 and power it On
            for ic, value in enumerate(ic_name_uri_list):
                ic_uri = ic_name_uri_list[ic]['uri']
                ic_name = ic_name_uri_list[ic]['name']
                name = ic_name_uri_list[ic]['enclosureName']
                if ic_name == "{}, interconnect 4".format(name):
                    logging.info("Powering on the carbon in {}".format(ic_name))
                    carbon_power_inst.PowerOnCarbon(ip, auth, api, ic_uri)
                    countdown(240)
                else:
                    pass
    
        countdown(540)
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
    
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnectMultiEnc(ip, auth, api, name)
            ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])
            # For loop to iterate thru carbon in bay1 and power it off
            logging.info("Power off the carbon ICMs in bay1")
            for ic, value in enumerate(ic_name_uri_list):
                ic_uri = ic_name_uri_list[ic]['uri']
                ic_name = ic_name_uri_list[ic]['name']
                name = ic_name_uri_list[ic]['enclosureName']
                if ic_name == "{}, interconnect 1".format(name):
                    logging.info("Powering off the carbon in {}".format(ic_name))
                    carbon_power_inst.PowerOffCarbon(ip, auth, api, ic_uri)
                else:
                    pass
    
        countdown(120)
        logging.info("Checking to see if carbons are actually turned off")
        tc = "Power turned off on carbon bay1"
        check_carbon_inst.IsCarbonTurnedOffBay1(ip, auth, api, enc_name)
        result = "Pass"
        PassOrFail(result, tc)
        logging.info("Waiting 3 minutes before powering on carbons in bay1.")
        countdown(180)
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnectMultiEnc(ip, auth, api, name)
            ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])
            # For loop to interate thru carbon in bay1 and power it On
            for ic, value in enumerate(ic_name_uri_list):
                ic_uri = ic_name_uri_list[ic]['uri']
                ic_name = ic_name_uri_list[ic]['name']
                name = ic_name_uri_list[ic]['enclosureName']
                if ic_name == "{}, interconnect 1".format(name):
                    logging.info("Powering on the carbon in {}".format(ic_name))
                    carbon_power_inst.PowerOnCarbon(ip, auth, api, ic_uri)
                    countdown(240)
                else:
                    pass
        
        countdown(540)
    
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        counter += 1
        countdown(30)
        logging.info("Starting next iteration")

def testcase_efuse_carbon(auth, tor_ip, enc_name):
    """
    1) Efuse carbon in bay1 for each enclosure
    2) wait 5 mins for each efuse operation on each carbon
    3) Flogi validation
    4) UL, DL, and carbon state validation
    5) ip address type validation
    6) Efuse carbon in bay4 for each enclosure
    7) wait 5 mins for each efuse operation on each carbon
    8) Flogi validation
    9) UL, DL, and carbon state validation
    10) ip address type validation
    """
    logging.testcases("##################################")
    logging.testcases("TestCase: Carbon Efuse stress test")
    logging.testcases("##################################")
    testcase = 'Carbon Efuse stress test'
    addr_type = "dhcp"
    logging.info("Checking the status of the downlink and uplink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    #Create Instances of Classes used in this script
    efuse_inst = EfuseResource()
    all_states_inst = CheckAllStatesOfCarbon()
    get_cbn_addr_type_inst = GetCarbonAddressType()
    get_num_flogi_inst = GetFLOGI()

    counter = 0
    # number = 5  Use this variable only when you want to run this tc for less iterations than the test suite.

    logging.info("Getting Enclosures ")
    enc_inst = Enclosures()
    enc_dict = enc_inst.GetEnc(ip, auth, api)
    enc_uri_list = printDict(enc_dict, ['uri', 'name'])

    countdown(5)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Efusing carbon(s) in Bay1")
        for i, value in enumerate(enc_uri_list):
            enc_uri = enc_uri_list[i]['uri']
            bay = "1"
            efuse_inst.EfuseCarbon(ip, auth, api, enc_uri, bay)
            countdown(300)
        countdown(300)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        get_cbn_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type, enc_name)

        countdown(30)
        logging.info("Pausing 30secs before moving on to bay4")
        logging.info("Efusing carbon in Bay4")
        for i, value in enumerate(enc_uri_list):
            enc_uri = enc_uri_list[i]['uri']
            bay = "4"
            print("executing function to efuse for bay4")
            efuse_inst.EfuseCarbon(ip, auth, api, enc_uri, bay)
            countdown(300)
        countdown(300)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        get_cbn_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type, enc_name)
        counter += 1
        countdown(30)


def testcase_restart_oneview(auth, tor_ip, enc_name):
    logging.testcases("############################")
    logging.testcases("TestCase: Restart of Oneview")
    logging.testcases("############################")

    testcase = 'Restart of Oneview'
    logging.info("Checking the status of the downlink and uplink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    # instantiation of Classes
    all_states_inst = CheckAllStatesOfCarbon()
    state_of_enc_inst = StateOfEnclosure()
    get_num_flogi_inst = GetFLOGI()

    counter = 0

    logging.info("Getting Enclosures ")
    enc_inst = Enclosures()

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("******************Restarting Oneview.  The restart takes about 45 mins.***********************")
        enc_inst.RestartOneview(ip, auth, api)
        countdown(2700)

        login_inst = LoginCreds()
        auth = login_inst.LoginToken(ip, api, username, ov_pw)

        # try:
        refresh_state = state_of_enc_inst.EncRefreshState(ip, auth, api)
        # except ConnectionError as e:
        #    print e
        #    logging.info("Could not connect to Oneview.")

        tc = "Refresh of Enclosure"
        if refresh_state == "NotRefreshing":
            logging.info("Enclosures is ready")
            result = "Pass"
            PassOrFail(result, tc)

        else:
            logging.error("The enclosure seems to still be refreshing, quitting script")
            result = "Fail"
            PassOrFail(result, tc)
            sys.exit(0)

        logging.info("Checking status of LE")
        GetStatusOfLogicalEnclosure(ip, auth, api)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        counter += 1


def testcase_icm_utilization(auth, enc_name):
    logging.testcases("#####################################")
    logging.testcases("TestCase: Carbon Utilization Samples")
    logging.testcases("#####################################")
    icm_util = Interconnects()
    icm_util.get_carbon_utilization(ip, auth, api, enc_name)


def testcase_remote_syslog(auth, enc_name):
    logging.testcases("###################################################")
    logging.testcases("TestCase: Enable/Disable RemoteSyslog Ipv4 and Ipv6")
    logging.testcases("###################################################")

    testcase = 'Enable/Disable RemoteSyslog Ipv4 and Ipv6'
    result = None
    logging.info("Checking the status of the downlink and uplink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    countdown(5)

    tc = "Enable RemoteSyslog Ipv6"
    remote_syslog_inst = RemoteSyslog()

    logging.info("Enable remote Syslog with IPv6 address")
    remote_syslog_inst.EnableRemoteSyslogIPv6(ip, auth, api)
    countdown(180)
    all_states_inst = CheckAllStatesOfCarbon()
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

    logging.info("Checking if remote Syslog is enabled")
    status = remote_syslog_inst.IsRemoteSyslogEnabled(ip, auth, api)

    if status:
        logging.info("Remote Syslog is enabled")
        result = "Pass"
    elif not status:
        logging.info("Remote Syslog is disabled")
        result = "Fail"
    else:
        logging.info("no condition was met")

    PassOrFail(result, tc)

    countdown(15)
    tc = "Disable RemoteSyslog Ipv6"
    logging.info("Disable remote Syslog with IPv6 address")
    remote_syslog_inst.DisableRemoteSyslogIPv6(ip, auth, api)
    countdown(180)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
    logging.info("Checking if remote Syslog is disabled")
    status = remote_syslog_inst.IsRemoteSyslogDisabled(ip, auth, api)
    if status:
        logging.info("Remote Syslog is enabled")
        result = "Fail"
    elif not status:
        logging.info("Remote Syslog is disabled")
        result = "Pass"
    else:
        logging.info("no condition was met")

    PassOrFail(result, tc)

    logging.info("Enable remote syslog with IPv4 address")
    tc = "Enable RemoteSyslog Ipv4"
    remote_syslog_inst.EnableRemoteSyslogIPv4(ip, auth, api)
    countdown(180)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
    logging.info("Checking if remote syslog is enabled")
    status = remote_syslog_inst.IsRemoteSyslogEnabled(ip, auth, api)
    if status:
        logging.info("Remote Syslog is enabled")
        result = "Pass"
    elif not status:
        logging.info("Remote Syslog is disabled")
        result = "Fail"
    else:
        logging.info("no condition was met")

    PassOrFail(result, tc)

    countdown(15)

    logging.info("Disable remote Syslog with IPv4 address\n")
    tc = "Disable RemoteSyslog Ipv4"
    remote_syslog_inst.DisableRemoteSyslogIPv4(ip, auth, api)
    countdown(180)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
    status = remote_syslog_inst.IsRemoteSyslogDisabled(ip, auth, api)
    if status:
        logging.info("Remote Syslog is enabled")
        result = "Fail"
    elif not status:
        logging.info("Remote Syslog is disabled")
        result = "Pass"
    else:
        logging.info("no condition was met")

    PassOrFail(result, tc)


def testcase_connectorinfo_digitaldiag(auth):
    logging.testcases("#######################################################")
    logging.testcases("testcase: Connector Information and Digital Diagnostics")
    logging.testcases("#######################################################")

    get_connector_diag_inst = ConnectorDigDiagInfo()
    logging.info("Getting Enclosure Group ")
    enclosure_inst = Enclosures()
    enc_dict = enclosure_inst.GetEnc(ip, auth, api)
    enc_name_list = printDict(enc_dict, ['name'])
    for x, value in enumerate(enc_name_list):
        enc_name = enc_name_list[x]['name']
        logging.info("Getting Interconnects")
        interconnect_dict = Interconnects()
        get_interconnect_list = interconnect_dict.GetInterconnectMultiEnc(ip, auth, api, enc_name)
        ic_model_list = printDict(get_interconnect_list, ['model', 'name', 'uri'])
        for ic, value in enumerate(ic_model_list):
            ic_uri = ic_model_list[ic]['uri']
            ic_name = ic_model_list[ic]['name']
            if ic_name == "{}, interconnect 1".format(enc_name):
                logging.testcases("The name of the carbon is {}".format(ic_name))
                connector_info = get_connector_diag_inst.GetInterconnectConnectorDigDiagInfo(ip, auth, api, ic_uri)
                for i, value in enumerate(connector_info):
                    ic_port_name = connector_info[i]['portName']
                    if ic_port_name == "Q3:1":
                        ic_port_vendor = connector_info[i]['vendorName']
                        tc = "Vendor Name for port {} is {}".format(ic_port_name, ic_port_vendor)
                        if ic_port_vendor != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_vendor_pn = connector_info[i]['vendorPartNumber']
                        tc = "Vendor PN for port {} is {}".format(ic_port_name, ic_port_vendor_pn)
                        if ic_port_vendor_pn != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_vendor_sn = connector_info[i]['serialNumber']
                        tc = "Vendor SN for port {} is {}".format(ic_port_name, ic_port_vendor_sn)
                        if ic_port_vendor_sn != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_identifier = connector_info[i]['identifier']
                        tc = "Port Identifier for port {} is {}".format(ic_port_name, ic_port_identifier)
                        if ic_port_identifier != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_dig_diag = connector_info[i]['digitalDiagnostics']
                        ic_port_dd_volt = ic_port_dig_diag['voltage']
                        tc = "voltage for port {} is {}".format(ic_port_name, ic_port_dd_volt)
                        if ic_port_dd_volt != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_dd_temp = ic_port_dig_diag['temperature']
                        tc = "Temperature for port {} is {}".format(ic_port_name, ic_port_dd_temp)
                        if ic_port_dd_temp != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_dd_lane = ic_port_dig_diag['laneInformation']
                        for i in range(0, len(ic_port_dd_lane)):
                            if ic_port_name == "Q3:1":
                                lane_id = ic_port_dd_lane[i]['laneId']
                                tc = "Lane ID for port {} is {}".format(ic_port_name, lane_id)
                                if lane_id != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                rx_power_mW = ic_port_dd_lane[i]['rxPowermW']
                                tc = "Rx PowermW for port {} is {}".format(ic_port_name, rx_power_mW)
                                if rx_power_mW != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                RxPowerBm = ic_port_dd_lane[i]['rxPowerdBm']
                                tc = "RxPowerBm for port {} is {}".format(ic_port_name, RxPowerBm)
                                if RxPowerBm != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                TxPowermW = ic_port_dd_lane[i]['txPowermW']
                                tc = "TxPowermW for port {} is {}".format(ic_port_name, TxPowermW)
                                if TxPowermW != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                TxPowerBm = ic_port_dd_lane[i]['txPowerdBm']
                                tc = "TxPowerBm for port {} is {}".format(ic_port_name, TxPowerBm)
                                if TxPowerBm != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                current = ic_port_dd_lane[i]['current']
                                tc = "current for port {} is {}".format(ic_port_name, current)
                                if current != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                    elif ic_port_name == '1':
                        ic_port_vendor = connector_info[i]['vendorName']
                        tc = "Vendor Name for port {} is {}".format(ic_port_name, ic_port_vendor)
                        if ic_port_vendor != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_vendor_pn = connector_info[i]['vendorPartNumber']
                        tc = "Vendor PN for port {} is {}".format(ic_port_name, ic_port_vendor_pn)
                        if ic_port_vendor_pn != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_vendor_sn = connector_info[i]['serialNumber']
                        tc = "Vendor SN for port {} is {}".format(ic_port_name, ic_port_vendor_sn)
                        if ic_port_vendor_sn != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_identifier = connector_info[i]['identifier']
                        tc = "Port Identifier for port {} is {}".format(ic_port_name, ic_port_identifier)
                        if ic_port_identifier != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_dig_diag = connector_info[i]['digitalDiagnostics']
                        ic_port_dd_volt = ic_port_dig_diag['voltage']
                        tc = "voltage for port {} is {}".format(ic_port_name, ic_port_dd_volt)
                        if ic_port_dd_volt != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_dd_temp = ic_port_dig_diag['temperature']
                        tc = "Temperature for port {} is {}".format(ic_port_name, ic_port_dd_temp)
                        if ic_port_dd_temp != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_dd_lane = ic_port_dig_diag['laneInformation']
                        if ic_port_name == "1":
                            for i in range(0, len(ic_port_dd_lane)):
                                lane_id = ic_port_dd_lane[i]['laneId']
                                tc = "Lane ID for port {} is {}".format(ic_port_name, lane_id)
                                if lane_id != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                rx_power_mW = ic_port_dd_lane[i]['rxPowermW']
                                tc = "rx_power_mW for port {} is {}".format(ic_port_name, rx_power_mW)
                                if rx_power_mW != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                rx_power_Bm = ic_port_dd_lane[i]['rxPowerdBm']
                                tc = "rx_power_Bm for port {} is {}".format(ic_port_name, rx_power_Bm)
                                if rx_power_Bm != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                tx_power_mW = ic_port_dd_lane[i]['txPowermW']
                                tc = "tx_power_mW for port {} is {}".format(ic_port_name, tx_power_mW)
                                if tx_power_mW != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                tx_power_Bm = ic_port_dd_lane[i]['txPowerdBm']
                                tc = "tx_power_Bm for port {} is {}".format(ic_port_name, tx_power_Bm)
                                if tx_power_Bm != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                current = ic_port_dd_lane[i]['current']
                                tc = "current for port {} is {}".format(ic_port_name, current)
                                if current != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
            if ic_name == "{}, interconnect 4".format(enc_name):
                logging.testcases("The name of the carbon is {}".format(ic_name))
                connector_info = get_connector_diag_inst.GetInterconnectConnectorDigDiagInfo(ip, auth, api, ic_uri)
                for i, value in enumerate(connector_info):
                    ic_port_name = connector_info[i]['portName']
                    if ic_port_name == "Q3:1":
                        ic_port_vendor = connector_info[i]['vendorName']
                        tc = "Vendor Name for port {} is {}".format(ic_port_name, ic_port_vendor)
                        if ic_port_vendor != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_vendor_pn = connector_info[i]['vendorPartNumber']
                        tc = "Vendor PN for port {} is {}".format(ic_port_name, ic_port_vendor_pn)
                        if ic_port_vendor_pn != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_vendor_sn = connector_info[i]['serialNumber']
                        tc = "Vendor SN for port {} is {}".format(ic_port_name, ic_port_vendor_sn)
                        if ic_port_vendor_sn != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_identifier = connector_info[i]['identifier']
                        tc = "Port Identifier for port {} is {}".format(ic_port_name, ic_port_identifier)
                        if ic_port_identifier != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_dig_diag = connector_info[i]['digitalDiagnostics']
                        ic_port_dd_volt = ic_port_dig_diag['voltage']
                        tc = "voltage for port {} is {}".format(ic_port_name, ic_port_dd_volt)
                        if ic_port_dd_volt != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_dd_temp = ic_port_dig_diag['temperature']
                        tc = "Temperature for port {} is {}".format(ic_port_name, ic_port_dd_temp)
                        if ic_port_dd_temp != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_dd_lane = ic_port_dig_diag['laneInformation']
                        for i in range(0, len(ic_port_dd_lane)):
                            if ic_port_name == "Q3:1":
                                lane_id = ic_port_dd_lane[i]['laneId']
                                tc = "Lane ID for port {} is {}".format(ic_port_name, lane_id)
                                if lane_id != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                rx_power_mW = ic_port_dd_lane[i]['rxPowermW']
                                tc = "Rx PowermW for port {} is {}".format(ic_port_name, rx_power_mW)
                                if rx_power_mW != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                rx_power_Bm = ic_port_dd_lane[i]['rxPowerdBm']
                                tc = "rx_power_Bm for port {} is {}".format(ic_port_name, rx_power_Bm)
                                if rx_power_Bm != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                tx_power_mW = ic_port_dd_lane[i]['txPowermW']
                                tc = "tx_power_mW for port {} is {}".format(ic_port_name, tx_power_mW)
                                if tx_power_mW != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                tx_power_Bm = ic_port_dd_lane[i]['txPowerdBm']
                                tc = "tx_power_Bm for port {} is {}".format(ic_port_name, tx_power_Bm)
                                if tx_power_Bm != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                current = ic_port_dd_lane[i]['current']
                                tc = "current for port {} is {}".format(ic_port_name, current)
                                if current != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                    elif ic_port_name == "1":
                        ic_port_vendor = connector_info[i]['vendorName']
                        tc = "Vendor Name for port {} is {}".format(ic_port_name, ic_port_vendor)
                        if ic_port_vendor != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_vendor_pn = connector_info[i]['vendorPartNumber']
                        tc = "Vendor PN for port {} is {}".format(ic_port_name, ic_port_vendor_pn)
                        if ic_port_vendor_pn != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_vendor_sn = connector_info[i]['serialNumber']
                        tc = "Vendor SN for port {} is {}".format(ic_port_name, ic_port_vendor_sn)
                        if ic_port_vendor_sn != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_identifier = connector_info[i]['identifier']
                        tc = "Port Identifier for port {} is {}".format(ic_port_name, ic_port_identifier)
                        if ic_port_identifier != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_dig_diag = connector_info[i]['digitalDiagnostics']
                        ic_port_dd_volt = ic_port_dig_diag['voltage']
                        tc = "voltage for port {} is {}".format(ic_port_name, ic_port_dd_volt)
                        if ic_port_dd_volt != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_dd_temp = ic_port_dig_diag['temperature']
                        tc = "Temperature for port {} is {}".format(ic_port_name, ic_port_dd_temp)
                        if ic_port_dd_temp != "null":
                            result = "Pass"
                            PassOrFail(result, tc)
                        else:
                            result = "Fail"
                            PassOrFail(result, tc)
                        ic_port_dd_lane = ic_port_dig_diag['laneInformation']
                        if ic_port_name == "1":
                            for i in range(0, len(ic_port_dd_lane)):
                                lane_id = ic_port_dd_lane[i]['laneId']
                                tc = "Lane ID for port {} is {}".format(ic_port_name, lane_id)
                                if lane_id != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                rx_power_mW = ic_port_dd_lane[i]['rxPowermW']
                                tc = "rx_power_mW for port {} is {}".format(ic_port_name, rx_power_mW)
                                if rx_power_mW != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                rx_power_Bm = ic_port_dd_lane[i]['rxPowerdBm']
                                tc = "rx_power_Bm for port {} is {}".format(ic_port_name, rx_power_Bm)
                                if rx_power_Bm != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                tx_power_mW = ic_port_dd_lane[i]['txPowermW']
                                tc = "tx_power_mW for port {} is {}".format(ic_port_name, tx_power_mW)
                                if tx_power_mW != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                tx_power_Bm = ic_port_dd_lane[i]['txPowerdBm']
                                tc = "tx_power_Bm for port {} is {}".format(ic_port_name, tx_power_Bm)
                                if tx_power_Bm != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                                current = ic_port_dd_lane[i]['current']
                                tc = "current for port {} is {}".format(ic_port_name, current)
                                if current != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
            else:
                pass


def testcase_staticIp_add_remove_encgrp(auth, tor_ip, enc_name):
    logging.testcases("#######################################################################")
    logging.testcases("testcase: Add/Remove IPv4 Static Address Range to/from Enclosure Group")
    logging.testcases("#######################################################################")
    network_id = '192.168.2.0'
    gateway = '192.168.2.1'
    start_address = '192.168.2.10'
    end_address = '192.168.2.254'
    testcase = 'Add/Remove IPv4 Static Address Range to/from Enclosure Group'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    countdown(5)

    all_states_inst = CheckAllStatesOfCarbon()
    ipv4_settings = ApplianceSettings()
    get_cbn_addr_type_inst = GetCarbonAddressType()
    get_num_flogi_inst = GetFLOGI()

    logging.info("Getting Enclosure Group ")
    enc_inst = Enclosures()
    enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
    enc_grp_list = printDict(enc_grp_dict, ['name', 'uri', 'eTag'])
    enc_grp_uri = enc_grp_list[0]['uri']
    enc_grp_etag = enc_grp_list[0]['eTag']

    logging.info("Getting list of LIGs")
    ligs_inst = LogicalInterconnectGroup()
    ligs_dict = ligs_inst.GetListOfLIGs(ip, auth, api)
    ligs_name_uri = printDict(ligs_dict, ['name', 'uri'])

    for i, value in enumerate(ligs_name_uri):
        lig_name = ligs_name_uri[i]['name']
        if lig_name == "LIG1":
            lig1_uri = ligs_name_uri[i]['uri']
        elif lig_name == "LIG2":
            lig2_uri = ligs_name_uri[i]['uri']
    update_enc_grp = UpdateEnclosureGroupME()


    logging.info("Creating IPv4 subnet ")
    ipv4_settings.CreateIPv4Subnet(ip, auth, api, network_id, gateway)
    logging.info("Getting ipv4 subnet")
    get_subnet = ipv4_settings.GetIPv4Subnet(ip, auth, api)
    subnet_list = printDict(get_subnet, ['uri', 'networkId'])
    networkid = [x for x in subnet_list if x['networkId'] == network_id]
    subnet_uri = networkid[0]['uri']
    logging.info("Creating ipv4 address range")
    ipv4_settings.CreateIPv4Range(ip, auth, api, start_address, end_address , subnet_uri)
    countdown(2)
    get_network = ipv4_settings.GetIPv4Subnet(ip, auth, api)
    ipv4_range = printDict(get_network, ['rangeUris', 'networkId'])
    network_range = [x for x in ipv4_range if x['networkId'] == network_id]
    range_uri_list = network_range[0]['rangeUris']
    range_uri = range_uri_list[0]
    logging.info("Updating Enclosure Group with Static IPv4 address range")
    update_enc_grp.UpdateEGIPv4RangeE28(ip, auth, api, enc_grp_uri, enc_grp_etag, range_uri, lig1_uri, lig2_uri)

    countdown(30)
    logging.info("*******************UPDATING LE ***************************")

    logging.info("Getting Logical Enclosure")
    le_inst = LogicalEnclosure()
    le_list = le_inst.GetLogicalEnclosure(ip, auth, api)
    le_uri_list = printDict(le_list, ['uri'])
    le_uri = le_uri_list[0]['uri']

    logging.info("Updating LE from group")
    update_le_inst = UpdateLogicalEnclosure()
    update_le_inst.LeUpdateFromGroup(ip, auth, api, le_uri)

    logging.info("Pausing for 15mins to wait for the LE to updated from group")
    countdown(900)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    addr_type = "static"
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
    get_cbn_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type, enc_name)

    countdown(30)

    logging.info("*******************RESETTING EG TO DEFAULT VALUES ***************************")

    logging.info("Getting list of LIGs")
    ligs_inst = LogicalInterconnectGroup()
    lig_list = ligs_inst.GetListOfLIGs(ip, auth, api)
    ligs_name_uri = printDict(lig_list, ['name', 'uri'])

    logging.info("Getting Enclosure Group ")
    enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
    enc_grp_list = printDict(enc_grp_dict, ['name', 'uri', 'eTag'])
    enc_grp_uri = enc_grp_list[0]['uri']
    enc_grp_etag = enc_grp_list[0]['eTag']

    for i, value in enumerate(ligs_name_uri):
        lig_name = ligs_name_uri[i]['name']
        if lig_name == "LIG1":
            lig1_uri = ligs_name_uri[i]['uri']
        elif lig_name == "LIG2":
            lig2_uri = ligs_name_uri[i]['uri']
    update_enc_grp.UpdateEGDefaultE28(ip, auth, api, enc_grp_uri, enc_grp_etag, lig1_uri, lig2_uri)

    logging.info("Pausing for 30 secs for EG to be created")
    countdown(20)

    logging.info("Updating LE from group")
    update_le_inst.LeUpdateFromGroup(ip, auth, api, le_uri)

    logging.info("********************UPDATE FROM GROUP THE LE***************************")

    logging.info("Pausing for 10mins for LE to be updated from group")
    countdown(600)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    addr_type = "dhcp"
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
    get_cbn_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type, enc_name)


def testcase_aside_bside_ligs(auth, tor_ip, enc_name):
    logging.testcases("########################################")
    logging.testcases("TestCase: UFG LE with A-Side B-side LIGs")
    logging.testcases("########################################")

    testcase = 'UFG LE with A-Side B-side LIGs'
    counter = 0

    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    countdown(5)

    enc_inst = Enclosures()
    all_states_inst = CheckAllStatesOfCarbon()
    power_cycle_server_inst = PowerOffOnServers()
    retrieve_net_inst = Networks()
    get_num_flogi_inst = GetFLOGI()

    logging.info("*******************CREATING LIGs ***************************")
    logging.info("Getting interconnect types uri")
    ic_types_dict = Interconnects()
    ic_types_list = ic_types_dict.GetInterconnectTypes(ip, auth, api)
    ic_types_name_uri = printDict(ic_types_list, ['uri', 'name'])

    logging.info("Getting Fc network URIs")
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc2_bay1uri, fc_net_enc2_bay4uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle28(
        ip, auth, api)

    create_lig_inst = CreateLogicalInterconnectGroupME()
    # Create Four LIGs(A-side and B-side) per enclosure with 1 uplink set per LIG in TBird enc.
    logging.info("Creating a LIGs")
    for s, value in enumerate(ic_types_name_uri):
        ic_uri = ic_types_name_uri[s]['uri']
        ic_name = ic_types_name_uri[s]['name']
        if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
            create_lig_inst.CreateLigASideEnc2E28(ip, auth, api, ic_uri, fc_net_enc2_bay1uri)
            create_lig_inst.CreateLigBSideEnc2E28(ip, auth, api, ic_uri, fc_net_enc2_bay4uri)
            create_lig_inst.CreateLigASideEnc1E28(ip, auth, api, ic_uri, fc_net_enc1_bay1_uri, fc_net_enc1_bay1_quri)
            create_lig_inst.CreateLigBSideEnc1E28(ip, auth, api, ic_uri, fc_net_enc1_bay4_uri)

    logging.info("Pausing 1min for the LIGs to be created")
    countdown(60)
    logging.info("*******************UPDATING EG ***************************")

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Getting list of LIGs")
        ligs_inst = LogicalInterconnectGroup()
        ligs_list = ligs_inst.GetListOfLIGs(ip, auth, api)
        ligs_name_uri = printDict(ligs_list, ['name', 'uri'])

        logging.info("Getting Enclosure Group ")
        enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
        enc_grp_list = printDict(enc_grp_dict, ['name', 'uri', 'eTag'])
        enc_grp_uri = enc_grp_list[0]['uri']
        enc_grp_etag = enc_grp_list[0]['eTag']

        for i, value in enumerate(ligs_name_uri):
            lig_name = ligs_name_uri[i]['name']
            if lig_name == "LIG_A-SIDE-ENC1":
                lig1_uri = ligs_name_uri[i]['uri']
            elif lig_name == "LIG_B-SIDE-ENC1":
                lig2_uri = ligs_name_uri[i]['uri']
            elif lig_name == "LIG_A-SIDE-ENC2":
                lig3_uri = ligs_name_uri[i]['uri']
            elif lig_name == "LIG_B-SIDE-ENC2":
                lig4_uri = ligs_name_uri[i]['uri']

        try:
            if lig_name == "LIG_A-SIDE-ENC1":
                lig1_uri = ligs_name_uri[i]['uri']
        except NameError as e:
            print (e)

        update_enc_grp = UpdateEnclosureGroupME()
        update_enc_grp.UpdateEgE28(ip, auth, api, enc_grp_uri, enc_grp_etag, lig1_uri, lig2_uri, lig3_uri, lig4_uri)

        logging.info("Pausing for 30 secs for EG to be updated")
        countdown(60)

        logging.info("Pausing for 3mins to power off servers")
        power_cycle_server_inst.power_off_servers(ip, auth, api)
        countdown(60)

        logging.info("*******************UPDATING LE ***************************")

        logging.info("Getting Logical Enclosure")
        le_inst = LogicalEnclosure()
        le_list = le_inst.GetLogicalEnclosure(ip, auth, api)
        le_uri_list = printDict(le_list, ['uri'])
        le_uri = le_uri_list[0]['uri']

        logging.info("Updating LE from group")
        update_le_inst = UpdateLogicalEnclosure()
        update_le_inst.LeUpdateFromGroup(ip, auth, api, le_uri)

        logging.info("Pausing for 20mins to wait for the LE to updated from group")
        countdown(1200)

        logging.info("Checking status of LE")
        GetStatusOfLogicalEnclosure(ip, auth, api)

        logging.info("Pausing for 7mins to power on servers")
        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(420)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


        logging.info("*******************RESETTING EG TO DEFAULT VALUES ***************************")

        for i, value in enumerate(ligs_name_uri):
            lig_name = ligs_name_uri[i]['name']
            if lig_name == "LIG1":
                lig_uri = ligs_name_uri[i]['uri']
            elif lig_name == "LIG2":
                lig1_uri = ligs_name_uri[i]['uri']

        logging.info("Getting Enclosure Group ")
        enc_inst = Enclosures()
        enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
        enc_grp_list = printDict(enc_grp_dict, ['name', 'uri', 'eTag'])
        enc_grp_uri = enc_grp_list[0]['uri']
        enc_grp_etag = enc_grp_list[0]['eTag']

        update_enc_grp.UpdateEGDefaultE28(ip, auth, api, enc_grp_uri, enc_grp_etag, lig_uri, lig1_uri)

        logging.info("Pausing for 30 secs for EG to be created")
        countdown(60)

        logging.info("Pausing for 3mins to power off servers")
        power_cycle_server_inst.power_off_servers(ip, auth, api)
        countdown(60)

        logging.info("********************UPDATE FROM GROUP THE LE***************************")

        logging.info("Updating LE from group")
        update_le_inst = UpdateLogicalEnclosure()
        update_le_inst.LeUpdateFromGroup(ip, auth, api, le_uri)

        logging.info("Pausing for 20mins for EG and LE to be updated from group")
        countdown(1200)

        logging.info("Checking status of LE")
        GetStatusOfLogicalEnclosure(ip, auth, api)
        countdown(10)

        logging.info("Pausing for 7mins to power on servers")
        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(420)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        counter += 1
        countdown(60)


def testcase_update_sp_speeds(auth, tor_ip, enc_name):
    logging.testcases("#######################################################")
    logging.testcases("TestCase: Server Profile FC Connection set to 16GB/Auto")
    logging.testcases("#######################################################")

    testcase = 'Server Profile FC Connection set to 16GB/Auto'
    counter = 0

    logging.info("Checking the status of the uplinks ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    sp_speeds_inst = ServerProfileConnectionSpeeds()
    all_states_inst = CheckAllStatesOfCarbon()
    power_cycle_server_inst = PowerOffOnServers()
    update_sp_inst = UpdateServerProfileBfsLunsNewDTO()
    retrieve_net_inst = Networks()
    get_num_flogi_inst = GetFLOGI()
    countdown(5)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Getting Fc network URIs")
        fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc2_bay1_uri, fc_net_enc2_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle28(
            ip, auth, api)

        power_cycle_server_inst.power_off_servers(ip, auth, api)
        countdown(30)

        logging.info("Getting Enclosure Group ")
        enc_inst = Enclosures()
        enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
        enc_grp_name_uri_list = printDict(enc_grp_dict, ['uri'])
        enc_grp_uri = enc_grp_name_uri_list[0]['uri']

        logging.info("Getting Server HW and Profiles")
        server_hw_profile_inst = Servers()
        sp_name, sp_descr, id_1, id_2 = server_hw_profile_inst.server_profile_config()
        sp_dict = server_hw_profile_inst.ServerProfiles(ip, auth, api)
        sp_list = printDict(sp_dict,
                            ['name', 'uri', 'serverHardwareUri', 'eTag', 'connectionSettings', 'serialNumber'])

        requested_bw = '16000'
        mode = "UEFI"

        for i, value in enumerate(sp_list):
            server_hw_uri = sp_list[i]['serverHardwareUri']
            sp_connection_settings = sp_list[i]['connectionSettings']
            sp_uri = sp_list[i]['uri']
            etag = sp_list[i]['eTag']
            sp_name = sp_list[i]['name']
            server_sn = sp_list[i]['serialNumber']
            conn_set = sp_connection_settings['connections']
            for x, value in enumerate(conn_set):
                if x == 0:
                    wwnn1 = conn_set[x]['wwnn']
                    wwpn1 = conn_set[x]['wwpn']
                elif x == 1:
                    wwnn2 = conn_set[x]['wwnn']
                    wwpn2 = conn_set[x]['wwpn']
            if server_sn == "MXQ94701Y9" or server_sn == "MXQ94701Y7" or server_sn == 'MXQ94701YC':
                update_sp_inst.UpdateServerProfileLunsEnc2(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                           sp_descr[i], requested_bw, fc_net_enc2_bay1_uri,
                                                           fc_net_enc2_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                           wwpn2, mode, etag)
            elif server_sn == "MXQ915012C" or server_sn == "MXQ94701Y5" or server_sn == "MXQ94701Y4":
                update_sp_inst.UpdateServerProfileLuns(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                       sp_descr[i], requested_bw, fc_net_enc1_bay1_uri,
                                                       fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                       wwpn2, mode, etag)
            countdown(10)

        logging.info("Pausing 7m30s for server profiles to be updated before powering on the servers")
        countdown(450)
        logging.info("*******************POWERING ON SERVERS **********************************")

        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(420)
        logging.info("Checking FC Connections are set to 16GB speed in Server Profiles")
        sp_speeds_inst.ServerProfileConnectionSpeed16GB(ip, auth, api)
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


        tc = "Update Server Profiles to 16Gb"
        logging.info("Checking status of server profiles")
        sp_status = GetSPStatus(ip, auth, api)
        if sp_status == "Normal":
            result = "Pass"
        else:
            result = "Fail"
        PassOrFail(result, tc)

        power_cycle_server_inst.power_off_servers(ip, auth, api)
        countdown(20)
        logging.info("*******************UPDATING SERVER PROFILES***************************")

        logging.info("Getting Server HW and Profiles")
        server_hw_profile_inst = Servers()
        sp_name, sp_descr, id_1, id_2 = server_hw_profile_inst.server_profile_config()
        sp_dict = server_hw_profile_inst.ServerProfiles(ip, auth, api)
        sp_list = printDict(sp_dict,
                            ['name', 'uri', 'serverHardwareUri', 'eTag', 'connectionSettings', 'serialNumber'])

        requested_bw = 'Auto'
        mode = "UEFI"

        for i, value in enumerate(sp_list):
            server_hw_uri = sp_list[i]['serverHardwareUri']
            sp_connection_settings = sp_list[i]['connectionSettings']
            sp_uri = sp_list[i]['uri']
            etag = sp_list[i]['eTag']
            sp_name = sp_list[i]['name']
            server_sn = sp_list[i]['serialNumber']
            conn_set = sp_connection_settings['connections']
            for x, value in enumerate(conn_set):
                if x == 0:
                    wwnn1 = conn_set[x]['wwnn']
                    wwpn1 = conn_set[x]['wwpn']
                elif x == 1:
                    wwnn2 = conn_set[x]['wwnn']
                    wwpn2 = conn_set[x]['wwpn']
            if server_sn == "MXQ94701Y9" or server_sn == "MXQ94701Y7" or server_sn == 'MXQ94701YC':
                update_sp_inst.UpdateServerProfileLunsEnc2(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                           sp_descr[i], requested_bw, fc_net_enc2_bay1_uri,
                                                           fc_net_enc2_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                           wwpn2, mode, etag)
            elif server_sn == "MXQ915012C" or server_sn == "MXQ94701Y5" or server_sn == "MXQ94701Y4":
                update_sp_inst.UpdateServerProfileLuns(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                       sp_descr[i], requested_bw, fc_net_enc1_bay1_uri,
                                                       fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                       wwpn2, mode, etag)
            countdown(10)

        logging.info("Pausing 7m30s for server profiles to be updated before powering on the servers")
        countdown(450)

        logging.info("*******************POWERING ON SERVERS **********************************")

        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(420)

        logging.info("Checking FC Connections are set to Auto speed in Server Profiles")
        sp_speeds_inst.ServerProfileConnectionSpeedAuto(ip, auth, api)
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


        tc = "Update Server Profiles to Auto"
        logging.info("Checking status of server profiles")
        sp_status = GetSPStatus(ip, auth, api)
        if sp_status == "Normal":
            result = "Pass"
        else:
            result = "Fail"
        PassOrFail(result, tc)

        counter += 1
        countdown(60)
        logging.info("Starting next iteration")


def testcase_add_remove_lig_enclosure_group(auth, tor_ip, enc_name):
    logging.testcases("################################################")
    logging.testcases("TestCase: Remove/Add LIG from/to Enclosure Group")
    logging.testcases("################################################")

    testcase = 'Remove/Add LIG from/to Enclosure Group'

    logging.info("Checking the status of the uplinks and downlink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    get_num_flogi_inst = GetFLOGI()
    all_states_inst = CheckAllStatesOfCarbon()
    countdown(5)

    logging.info("Getting Enclosure Group ")
    enc_inst = Enclosures()
    enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
    enc_grp_list = printDict(enc_grp_dict, ['name', 'uri', 'eTag'])
    enc_grp_uri = enc_grp_list[0]['uri']
    enc_grp_etag = enc_grp_list[0]['eTag']

    logging.info("Getting list of LIGs")
    ligs_inst = LogicalInterconnectGroup()
    ligs_list = ligs_inst.GetListOfLIGs(ip, auth, api)
    ligs_name_uri = printDict(ligs_list, ['name', 'uri'])

    for i, value in enumerate(ligs_name_uri):
        lig_name = ligs_name_uri[i]['name']
        if lig_name == "LIG1":
            lig1_uri = ligs_name_uri[i]['uri']
        elif lig_name == "LIG2":
            lig2_uri = ligs_name_uri[i]['uri']

    update_enc_grp = UpdateEnclosureGroupME()

    # Function to update EG with no LIGs
    logging.info("**********Removing LIGs from Enclosure Group**************")
    update_enc_grp.UpdateEgNoLigsE28(ip, auth, api, enc_grp_uri, enc_grp_etag)
    countdown(20)

    logging.info("*******************UPDATING LE ***************************")

    logging.info("Getting Logical Enclosure")
    le_inst = LogicalEnclosure()
    le_list = le_inst.GetLogicalEnclosure(ip, auth, api)
    le_uri_list = printDict(le_list, ['uri'])
    le_uri = le_uri_list[0]['uri']

    logging.info("Updating LE from group")
    update_le_inst = UpdateLogicalEnclosure()
    update_le_inst.LeUpdateFromGroup(ip, auth, api, le_uri)

    logging.info("Pausing for 10mins to wait for the LE to updated from group")
    countdown(600)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    logging.info("*******************RESETTING EG TO DEFAULT VALUES ***************************")

    logging.info("Getting list of LIGs")
    ligs_inst = LogicalInterconnectGroup()
    ligs_list = ligs_inst.GetListOfLIGs(ip, auth, api)
    ligs_name_uri = printDict(ligs_list, ['name', 'uri'])

    logging.info("Getting Enclosure Group ")
    enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
    enc_grp_list = printDict(enc_grp_dict, ['name', 'uri', 'eTag'])
    enc_grp_uri = enc_grp_list[0]['uri']
    enc_grp_etag = enc_grp_list[0]['eTag']

    for i in range(0, len(ligs_name_uri)):
        lig_name = ligs_name_uri[i]['name']
        if lig_name == "LIG1":
            lig1_uri = ligs_name_uri[i]['uri']
        elif lig_name == "LIG2":
            lig2_uri = ligs_name_uri[i]['uri']
    update_enc_grp.UpdateEGDefaultE28(ip, auth, api, enc_grp_uri, enc_grp_etag, lig1_uri, lig2_uri)

    logging.info("Pausing for 30 secs for EG to be created")
    countdown(20)

    logging.info("Updating LE from group")
    update_le_inst.LeUpdateFromGroup(ip, auth, api, le_uri)

    logging.info("********************UPDATE FROM GROUP THE LE***************************")

    logging.info("Pausing for 10mins for LE to be updated from group")
    countdown(300)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    countdown(300)

    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


    countdown(120)


def testcase_change_port_speeds_tor(auth, tor_ip, enc_name):
    logging.testcases("#######################################################")
    logging.testcases("TestCase: Change port speeds(4/8/16GB) on ToR FC switch")
    logging.testcases("#######################################################")

    counter = 0
    testcase = 'Change port speeds(4/8/16GB) on ToR FC switch'
    logging.info("Checking the status of the downlink and uplink ports before starting the test")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    port_speeds_inst = ConfigureTOR()
    carbon_port_speeds_inst = GetCarbonPortStatus()
    get_num_flogi_inst = GetFLOGI()
    all_states_inst = CheckAllStatesOfCarbon()
    countdown(5)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.testcases("Port speed set to 4Gb")
        port_speeds_inst.ConfigPortSpeed4GbE28TORPort24_27(tor_ip, tor_un, tor_pw)
        countdown(120)
        carbon_port_speeds_inst.GetCarbonUpLinkQ3PortSpeed4Gb(ip, api, auth)

        logging.testcases("Port speed set to 8Gb")
        port_speeds_inst.ConfigPortSpeed8GbE28TORPort24_27(tor_ip, tor_un, tor_pw)
        countdown(120)
        carbon_port_speeds_inst.GetCarbonUpLinkQ3PortSpeed8Gb(ip, api, auth)

        logging.testcases("Port speed set to 16Gb")
        port_speeds_inst.ConfigPortSpeed16GbE28TORPort24_27(tor_ip, tor_un, tor_pw)
        countdown(120)
        carbon_port_speeds_inst.GetCarbonUpLinkQ3PortSpeed16Gb(ip, api, auth)

        logging.testcases("Port speed set to Auto")
        port_speeds_inst.ConfigPortSpeedAutoE28TORPort24_27(tor_ip, tor_un, tor_pw)
        countdown(120)
        carbon_port_speeds_inst.GetCarbonUpLinkQ3PortSpeed16Gb(ip, api, auth)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        counter += 1
        countdown(60)


def testcase_remove_add_fcnetwork_lig_bad(auth, tor_ip, enc_name):
    logging.testcases("##################################################")
    logging.testcases("TestCase: Remove/Add FC Network from ULS from LIG ")
    logging.testcases("##################################################")
    counter = 0
    testcase = 'Remove/Add FC Network from ULS from LIG'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    retrieve_net_inst = Networks()
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()

    logging.info("Getting Fc network URIs")
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc2_bay1_uri, fc_net_enc2_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle28(
        ip, auth, api)
    logging.info("Getting Uplink sets URIs")
    uls_enc1_bay1_uri, uls_enc1_bay4_uri, uls_enc2_bay1_uri, uls_enc2_bay4_uri = retrieve_net_inst.get_uplink_set_uri_eagle28(
        ip, auth, api)

    countdown(5)

    logging.info("Getting Logical Interconnects")
    li_instance = LogicalInterconnects()
    li_dict = li_instance.GetLogicalInterconnects(ip, auth, api)
    li_name_uri_list = printDict(li_dict, ['uri', 'name'])
    for n, value in enumerate(li_name_uri_list):
        li_name = li_name_uri_list[n]['name']
        li_uri = li_name_uri_list[n]['uri']
        if li_name == "LE-LIG1-1":
            li_uri1 = li_uri
        elif li_name == "LE-LIG2-1":
            li_uri2 = li_uri
        elif li_name == "LE-LIG2-2":
            li_uri2 = li_uri

    uplink_sets_inst = AddRemoveUplinkSetsLiME()

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Getting Enclosures ")

        logging.info("Getting interconnect types uri")
        ic_types_dict = Interconnects()
        ic_types_list = ic_types_dict.GetInterconnectTypes(ip, auth, api)
        ic_types_name_uri = printDict(ic_types_list, ['uri', 'name'])

        retrieve_net_inst = Networks()
        fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc2_bay1uri, fc_net_enc2_bay4uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle28(
            ip, auth, api)

        logging.info("Getting list of LIGs")
        ligs_inst = LogicalInterconnectGroup()
        ligs_list = ligs_inst.GetListOfLIGs(ip, auth, api)
        ligs_name_uri = printDict(ligs_list, ['name', 'uri', 'eTag'])

        for i, value in enumerate(ligs_name_uri):
            lig_name = ligs_name_uri[i]['name']
            ligs_uri = ligs_name_uri[i]['uri']
            if lig_name == "LIG1":
                lig1_uri = ligs_uri
            elif lig_name == "LIG2":
                lig2_uri = ligs_uri
            else:
                pass
        update_lig_inst = UpdateLogicalInterconnectGroupME()
        lig_name_list = ('LIG1', 'LIG2')
        logging.info("Updating 2 LIGs, each LIG with uplink set with no FC network in bay1")
        logging.info("Entering into LIG Loop")

        for s, value in enumerate(ic_types_name_uri):
            ic_uri = ic_types_name_uri[s]['uri']
            lig_name = lig_name_list[1]
            update_lig_inst = UpdateLogicalInterconnectGroupME()
            update_lig_inst.UpdateLig2E28NoFcNetBay1(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay4uri, lig2_uri,
                                                     consistency_check, v3_enabled)
            lig_name = lig_name_list[0]
            update_lig_inst.UpdateLigE28NoFcNetBay1(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay4_uri, lig1_uri,
                                                    consistency_check, v3_enabled)

        logging.info("Updating LIGs")
        countdown(30)

        uplink_sets_inst.RemoveUlsBay1FcNetworkLiEnc1(ip, auth, api, li_uri1, enc1_uri, uls_enc1_bay1_uri)
        logging.info("Removing FC network from BAY1-EAGLE28 uplink set")

        uplink_sets_inst.RemoveUlsBay1FcNetworkLiEnc2(ip, auth, api, li_uri2, enc2_uri, uls_enc2_bay1_uri)
        logging.info("Removing FC network from BAY1-EAGLE29 uplink set")

        countdown(420)

        lig_name_list = ('LIG1', 'LIG2')

        logging.info("Updating 2 LIGs back to their default settings")
        logging.info("Entering into LIG Loop")

        for s, value in enumerate(ic_types_name_uri):
            ic_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                lig_name = lig_name_list[1]
                update_lig_inst.UpdateLigTwoE28Default(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay1uri,
                                                       fc_net_enc2_bay4uri, lig2_uri, consistency_check, v3_enabled)
                lig_name = lig_name_list[0]
                update_lig_inst.UpdateLigE28Default(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay1_uri,
                                                    fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, lig1_uri,
                                                    consistency_check, v3_enabled)

        countdown(30)

        uplink_sets_inst.AddUlsBay1FcNetworkLiEnc1(ip, auth, api, fc_net_enc1_bay1_uri, li_uri1, enc1_uri,
                                                   uls_enc1_bay1_uri)
        logging.info(
            "Adding FC network back to BAY1-EAGLE28 uplink set and Pausing for 7mins before check state and downlink ports on carbons")
        uplink_sets_inst.AddUlsBay1FcNetworkLiEnc2(ip, auth, api, fc_net_enc2_bay1_uri, li_uri2, enc2_uri,
                                                   uls_enc2_bay1_uri)
        logging.info("Adding FC network back to BAY1-EAGLE29 uplink set")
        countdown(420)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        logging.info("Updating 2 LIGs, each LIG with uplink set with no FC network in bay4")
        logging.info("Entering into LIG Loop")

        for s, value in enumerate(ic_types_name_uri):
            ic_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                lig_name = lig_name_list[1]
                update_lig_inst.UpdateLig2E28NoFcNetBay4(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay1uri, lig2_uri,
                                                         consistency_check, v3_enabled)
                lig_name = lig_name_list[0]
                update_lig_inst.UpdateLigE28NoFcNetBay4(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay1_uri, lig1_uri,
                                                        consistency_check, v3_enabled)

        logging.info("Updating LIGs")
        countdown(30)

        uplink_sets_inst.RemoveUlsBay4FcNetworkLiEnc1(ip, auth, api, li_uri1, enc1_uri, uls_enc1_bay4_uri)
        logging.info("Removing FC network from BAY4-EAGLE28 uplink set")
        uplink_sets_inst.RemoveUlsBay4FcNetworkLiEnc2(ip, auth, api, li_uri2, enc2_uri, uls_enc2_bay4_uri)
        logging.info("Removing FC network from BAY4-EAGLE29 uplink set")
        countdown(420)

        lig_name_list = ('LIG1', 'LIG2')

        logging.info("Updating 2 LIGs back to their default settings")
        logging.info("Entering into LIG Loop")

        for s, value in enumerate(ic_types_name_uri):
            ic_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                lig_name = lig_name_list[1]
                update_lig_inst.UpdateLigTwoE28Default(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay1uri,
                                                       fc_net_enc2_bay4uri, lig2_uri, consistency_check, v3_enabled)
                lig_name = lig_name_list[0]
                update_lig_inst.UpdateLigE28Default(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay1_uri,
                                                    fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, lig1_uri,
                                                    consistency_check, v3_enabled)

        countdown(30)

        uplink_sets_inst.AddUlsBay4FcNetworkLiEnc1(ip, auth, api, fc_net_enc1_bay4_uri, li_uri1, enc1_uri,
                                                   uls_enc1_bay4_uri)
        logging.info("Adding FC network back to BAY4-EAGLE28 uplink set")
        uplink_sets_inst.AddUlsBay4FcNetworkLiEnc2(ip, auth, api, fc_net_enc2_bay4_uri, li_uri2, enc2_uri,
                                                   uls_enc2_bay4_uri)
        logging.info("Adding FC network back to BAY4-EAGLE29 uplink set")
        countdown(420)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        counter += 1
        countdown(60)


def testcase_remove_add_fcnetwork_lig(auth, tor_ip, enc_name):
    logging.testcases("##################################################")
    logging.testcases("TestCase: Remove/Add FC Network from ULS from LIG ")
    logging.testcases("##################################################")
    counter = 0
    testcase = 'Remove/Add FC Network from ULS from LIG'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    retrieve_net_inst = Networks()
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()

    logging.info("Getting Fc network URIs")
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc2_bay1_uri, fc_net_enc2_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle28(
        ip, auth, api)
    logging.info("Getting Uplink sets URIs")
    uls_enc1_bay1_uri, uls_enc1_bay4_uri, uls_enc2_bay1_uri, uls_enc2_bay4_uri = retrieve_net_inst.get_uplink_set_uri_eagle28(
        ip, auth, api)

    countdown(5)

    logging.info("Getting Logical Interconnects")
    li_instance = LogicalInterconnects()
    li_dict = li_instance.GetLogicalInterconnects(ip, auth, api)
    li_name_uri_list = printDict(li_dict, ['uri', 'name'])
    for n, value in enumerate(li_name_uri_list):
        li_name = li_name_uri_list[n]['name']
        li_uri = li_name_uri_list[n]['uri']
        if li_name == "LE-LIG1-1":
            li_uri1 = li_uri
        elif li_name == "LE-LIG2-1":
            li_uri2 = li_uri
        elif li_name == "LE-LIG2-2":
            li_uri2 = li_uri

    uplink_sets_inst = AddRemoveUplinkSetsLiME()

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Getting Enclosures ")
        enc_inst = Enclosures()
        enc_dict = enc_inst.GetEnc(ip, auth, api)
        enc_name_uri_list = printDict(enc_dict, ['enclosureModel', 'name', 'uri'])

        logging.info("Getting interconnect types uri")
        ic_types_dict = Interconnects()
        ic_types_list = ic_types_dict.GetInterconnectTypes(ip, auth, api)
        ic_types_name_uri = printDict(ic_types_list, ['uri', 'name'])

        retrieve_net_inst = Networks()
        fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc2_bay1uri, fc_net_enc2_bay4uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle28(
            ip, auth, api)

        logging.info("Getting list of LIGs")
        ligs_inst = LogicalInterconnectGroup()
        ligs_list = ligs_inst.GetListOfLIGs(ip, auth, api)
        ligs_name_uri = printDict(ligs_list, ['name', 'uri', 'eTag'])

        for i, value in enumerate(ligs_name_uri):
            lig_name = ligs_name_uri[i]['name']
            ligs_uri = ligs_name_uri[i]['uri']
            if lig_name == "LIG1":
                lig1_uri = ligs_uri
            elif lig_name == "LIG2":
                lig2_uri = ligs_uri
            else:
                pass

        lig_name_list = ('LIG1', 'LIG2')
        logging.info("Updating 2 LIGs, each LIG with uplink set with no FC network in bay1")
        logging.info("Entering into LIG Loop")
        update_lig_inst = UpdateLogicalInterconnectGroupME()
        for i, value in enumerate(enc_name_uri_list):
            name = enc_name_uri_list[i]['name']
            if name == "%s" % enc_two:
                lig_name = lig_name_list[1]
                for s, value in enumerate(ic_types_name_uri):
                    ic_uri = ic_types_name_uri[s]['uri']
                    ic_name = ic_types_name_uri[s]['name']
                    if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                        update_lig_inst.UpdateLig2E28NoFcNetBay1(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay4uri,
                                                                 lig2_uri, consistency_check, v3_enabled)

            elif name == "%s" % enc_one:
                lig_name = lig_name_list[0]
                for s, value in enumerate(ic_types_name_uri):
                    ic_uri = ic_types_name_uri[s]['uri']
                    ic_name = ic_types_name_uri[s]['name']
                    if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                        update_lig_inst.UpdateLigE28NoFcNetBay1(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay4_uri,
                                                                lig1_uri, consistency_check, v3_enabled)

        logging.info("Updating LIGs")
        countdown(30)

        uplink_sets_inst.RemoveUlsBay1FcNetworkLiEnc1(ip, auth, api, li_uri1, enc1_uri, uls_enc1_bay1_uri)
        logging.info("Removing FC network from BAY1-EAGLE28 uplink set")

        uplink_sets_inst.RemoveUlsBay1FcNetworkLiEnc2(ip, auth, api, li_uri2, enc2_uri, uls_enc2_bay1_uri)
        logging.info("Removing FC network from BAY1-EAGLE29 uplink set")

        countdown(420)

        lig_name_list = ('LIG1', 'LIG2')

        logging.info("Updating 2 LIGs back to their default settings")
        logging.info("Entering into LIG Loop")

        for i, value in enumerate(enc_name_uri_list):
            name = enc_name_uri_list[i]['name']
            if name == "%s" % enc_two:
                lig_name = lig_name_list[1]
                for s, value in enumerate(ic_types_name_uri):
                    ic_uri = ic_types_name_uri[s]['uri']
                    ic_name = ic_types_name_uri[s]['name']
                    if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                        update_lig_inst.UpdateLigTwoE28Default(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay1uri,
                                                               fc_net_enc2_bay4uri, lig2_uri, consistency_check,
                                                               v3_enabled)

            elif name == "%s" % enc_one:
                lig_name = lig_name_list[0]
                for s, value in enumerate(ic_types_name_uri):
                    ic_uri = ic_types_name_uri[s]['uri']
                    ic_name = ic_types_name_uri[s]['name']
                    if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                        update_lig_inst.UpdateLigE28Default(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay1_uri,
                                                            fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, lig1_uri,
                                                            consistency_check, v3_enabled)

        countdown(30)

        uplink_sets_inst.AddUlsBay1FcNetworkLiEnc1(ip, auth, api, fc_net_enc1_bay1_uri, li_uri1, enc1_uri,
                                                   uls_enc1_bay1_uri)
        logging.info(
            "Adding FC network back to BAY1-EAGLE28 uplink set and Pausing for 7mins before check state and downlink ports on carbons")
        uplink_sets_inst.AddUlsBay1FcNetworkLiEnc2(ip, auth, api, fc_net_enc2_bay1_uri, li_uri2, enc2_uri,
                                                   uls_enc2_bay1_uri)
        logging.info("Adding FC network back to BAY1-EAGLE29 uplink set")
        countdown(420)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        logging.info("Updating 2 LIGs, each LIG with uplink set with no FC network in bay4")
        logging.info("Entering into LIG Loop")

        for i, value in enumerate(enc_name_uri_list):
            name = enc_name_uri_list[i]['name']
            if name == "%s" % enc_two:
                lig_name = lig_name_list[1]
                for s, value in enumerate(ic_types_name_uri):
                    ic_uri = ic_types_name_uri[s]['uri']
                    ic_name = ic_types_name_uri[s]['name']
                    if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                        update_lig_inst.UpdateLig2E28NoFcNetBay4(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay1uri,
                                                                 lig2_uri, consistency_check, v3_enabled)

            elif name == "%s" % enc_one:
                lig_name = lig_name_list[0]
                for s, value in enumerate(ic_types_name_uri):
                    ic_uri = ic_types_name_uri[s]['uri']
                    ic_name = ic_types_name_uri[s]['name']
                    if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                        update_lig_inst.UpdateLigE28NoFcNetBay4(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay1_uri,
                                                                lig1_uri, consistency_check, v3_enabled)

        logging.info("Updating LIGs")
        countdown(30)

        uplink_sets_inst.RemoveUlsBay4FcNetworkLiEnc1(ip, auth, api, li_uri1, enc1_uri, uls_enc1_bay4_uri)
        logging.info("Removing FC network from BAY4-EAGLE28 uplink set")
        uplink_sets_inst.RemoveUlsBay4FcNetworkLiEnc2(ip, auth, api, li_uri2, enc2_uri, uls_enc2_bay4_uri)
        logging.info("Removing FC network from BAY4-EAGLE29 uplink set")
        countdown(420)

        lig_name_list = ('LIG1', 'LIG2')

        logging.info("Updating 2 LIGs back to their default settings")
        logging.info("Entering into LIG Loop")

        for i, value in enumerate(enc_name_uri_list):
            name = enc_name_uri_list[i]['name']
            if name == "%s" % enc_two:
                lig_name = lig_name_list[1]
                for s, value in enumerate(ic_types_name_uri):
                    ic_uri = ic_types_name_uri[s]['uri']
                    ic_name = ic_types_name_uri[s]['name']
                    if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                        update_lig_inst.UpdateLigTwoE28Default(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay1uri,
                                                               fc_net_enc2_bay4uri, lig2_uri, consistency_check,
                                                               v3_enabled)

            elif name == "%s" % enc_one:
                lig_name = lig_name_list[0]
                for s, value in enumerate(ic_types_name_uri):
                    ic_uri = ic_types_name_uri[s]['uri']
                    ic_name = ic_types_name_uri[s]['name']
                    if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                        update_lig_inst.UpdateLigE28Default(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay1_uri,
                                                            fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, lig1_uri,
                                                            consistency_check, v3_enabled)

        countdown(30)

        uplink_sets_inst.AddUlsBay4FcNetworkLiEnc1(ip, auth, api, fc_net_enc1_bay4_uri, li_uri1, enc1_uri,
                                                   uls_enc1_bay4_uri)
        logging.info("Adding FC network back to BAY4-EAGLE28 uplink set")
        uplink_sets_inst.AddUlsBay4FcNetworkLiEnc2(ip, auth, api, fc_net_enc2_bay4_uri, li_uri2, enc2_uri,
                                                   uls_enc2_bay4_uri)
        logging.info("Adding FC network back to BAY4-EAGLE29 uplink set")
        countdown(240)

        logging.info("*******************UPDATING LE ***************************")

        logging.info("Getting Logical Enclosure")
        le_inst = LogicalEnclosure()
        le_list = le_inst.GetLogicalEnclosure(ip, auth, api)
        le_uri_list = printDict(le_list, ['uri'])
        le_uri = le_uri_list[0]['uri']

        logging.info("Updating LE from group")
        update_le_inst = UpdateLogicalEnclosure()
        update_le_inst.LeUpdateFromGroup(ip, auth, api, le_uri)
        countdown(420)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        counter += 1
        countdown(60)


def testcase_disable_enable_trunking_lig(auth, tor_ip, enc_name):
    logging.testcases("########################################")
    logging.testcases("TestCase: Disable/Enable Trunking on LIG")
    logging.testcases("########################################")
    testcase = 'Disable/Enable Trunking on LIG'

    counter = 0
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    update_li_inst = UpdateLogicalInterconnects()
    trunking = ConfigureTOR()
    retrieve_net_inst = Networks()
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()

    countdown(2)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Disable trunking on TOR switch")
        trunking.DisableTrunkingOnE28TORPort32_33(tor_ip, tor_un, tor_pw)
        trunking.DisableTrunkingOnE28TORPort8_10(tor_ip, tor_un, tor_pw)
        trunking.DisableTrunkingOnE28TORPort24_27(tor_ip, tor_un, tor_pw)
        trunking.DisableTrunkingOnE28TORPort40_41(tor_ip, tor_un, tor_pw)

        countdown(120)

        logging.info("Getting interconnect types uri")
        ic_types_instance = Interconnects()
        ic_types_dict = ic_types_instance.GetInterconnectTypes(ip, auth, api)
        ic_types_name_uri = printDict(ic_types_dict, ['uri', 'name'])

        logging.info("Getting list of LIGs")
        ligs_inst = LogicalInterconnectGroup()
        ligs_dict = ligs_inst.GetListOfLIGs(ip, auth, api)
        ligs_name_uri = printDict(ligs_dict, ['name', 'uri'])

        for i, value in enumerate(ligs_name_uri):
            lig_name = ligs_name_uri[i]['name']
            if lig_name == "LIG1":
                lig1_uri = ligs_name_uri[i]['uri']
            elif lig_name == "LIG2":
                lig2_uri = ligs_name_uri[i]['uri']

        logging.info("Getting Fc network URIs")
        fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc2_bay1_uri, fc_net_enc2_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle28(
            ip, auth, api)

        lig_name_list = ('LIG1', 'LIG2')
        fc_mode = 'NONE'
        update_lig_inst = UpdateLogicalInterconnectGroupME()
        # Create 2 LIGs with 2 uplink sets in TBird enc.
        logging.info("Entering into LIG Loop")
        for s, value in enumerate(ic_types_name_uri):
            ic_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                lig_name = lig_name_list[1]
                update_lig_inst = UpdateLogicalInterconnectGroupME()
                update_lig_inst.UpdateLig2TrunkE28(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay1_uri,
                                                   fc_net_enc2_bay4_uri, lig2_uri, fc_mode, v3_enabled,
                                                   consistency_check)
                lig_name = lig_name_list[0]
                update_lig_inst.UpdateLig1TrunkE28(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay1_uri,
                                                   fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, lig1_uri, fc_mode,
                                                   v3_enabled, consistency_check)

        logging.info("Updating LIGs with trunking disabled")
        countdown(15)

        logging.info("Getting Logical Interconnects")
        li_instance = LogicalInterconnects()
        li_dict = li_instance.GetLogicalInterconnects(ip, auth, api)
        li_name_uri_list = printDict(li_dict, ['uri', 'name'])

        logging.info("Updating LI from group")
        for i, value in enumerate(li_name_uri_list):
            logging.info("Updating {} from LIG".format(li_name_uri_list[i]['name']))
            li_uri = li_name_uri_list[i]['uri']
            update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

        countdown(420)

        logging.info("Checking status of LE")
        GetStatusOfLogicalEnclosure(ip, auth, api)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        logging.info("Updating LIGs with trunking enabled")
        fc_mode = 'TRUNK'

        for s, value in enumerate(ic_types_name_uri):
            ic_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                lig_name = lig_name_list[1]
                update_lig_inst.UpdateLig2TrunkE28(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay1_uri,
                                                   fc_net_enc2_bay4_uri, lig2_uri, fc_mode, v3_enabled,
                                                   consistency_check)
                lig_name = lig_name_list[0]
                update_lig_inst.UpdateLig1TrunkE28(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay1_uri,
                                                   fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, lig1_uri, fc_mode,
                                                   v3_enabled, consistency_check)

        countdown(15)

        logging.info("Getting Logical Interconnects")
        li_instance = LogicalInterconnects()
        li_dict = li_instance.GetLogicalInterconnects(ip, auth, api)
        li_name_uri_list = printDict(li_dict, ['uri', 'name'])

        logging.info("Updating LI from group")
        for i, value in enumerate(li_name_uri_list):
            logging.info("Updating {} from LIG".format(li_name_uri_list[i]['name']))
            li_uri = li_name_uri_list[i]['uri']
            update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

        countdown(420)

        logging.info("Checking status of LE")
        GetStatusOfLogicalEnclosure(ip, auth, api)

        logging.info("Enable trunking on TOR switch")
        trunking.EnableTrunkingOnE28TORPort32_33(tor_ip, tor_un, tor_pw)
        trunking.EnableTrunkingOnE28TORPort8_10(tor_ip, tor_un, tor_pw)
        trunking.EnableTrunkingOnE28TORPort24_27(tor_ip, tor_un, tor_pw)
        trunking.EnableTrunkingOnE28TORPort40_41(tor_ip, tor_un, tor_pw)

        countdown(120)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


        logging.info("Updating LIGs with various speeds set on uplink ports")

        for s, value in enumerate(ic_types_name_uri):
            ic_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                lig_name = lig_name_list[1]
                update_lig_inst.UpdateLig2VariousSpeedsE28(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay1_uri,
                                                           fc_net_enc2_bay4_uri, lig2_uri, fc_mode, v3_enabled,
                                                           consistency_check)
                lig_name = lig_name_list[0]
                update_lig_inst.UpdateLig1VariousSpeedsE28(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay1_uri,
                                                           fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, lig1_uri,
                                                           fc_mode, v3_enabled, consistency_check)

        countdown(15)

        logging.info("Getting Logical Interconnects")
        li_instance = LogicalInterconnects()
        li_dict = li_instance.GetLogicalInterconnects(ip, auth, api)
        li_name_uri_list = printDict(li_dict, ['uri', 'name'])

        logging.info("Updating LI from group")
        for i, value in enumerate(li_name_uri_list):
            logging.info("Updating {} from LIG".format(li_name_uri_list[i]['name']))
            li_uri = li_name_uri_list[i]['uri']
            update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

        countdown(420)

        logging.info("Checking status of LE")
        GetStatusOfLogicalEnclosure(ip, auth, api)

        testcase = "Speed set to 4Gb/8Gb/16Gb with trunking Enabled"
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


        logging.info("Resetting the LIGs to default settings")
        for s, value in enumerate(ic_types_name_uri):
            ic_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                lig_name = lig_name_list[1]
                update_lig_inst.UpdateLig2TrunkE28(ip, auth, api, lig_name, ic_uri, fc_net_enc2_bay1_uri,
                                                   fc_net_enc2_bay4_uri, lig2_uri, fc_mode, v3_enabled,
                                                   consistency_check)
                lig_name = lig_name_list[0]
                update_lig_inst.UpdateLig1TrunkE28(ip, auth, api, lig_name, ic_uri, fc_net_enc1_bay1_uri,
                                                   fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, lig1_uri, fc_mode,
                                                   v3_enabled, consistency_check)

        countdown(30)

        logging.info("Getting Logical Interconnects")
        li_instance = LogicalInterconnects()
        li_dict = li_instance.GetLogicalInterconnects(ip, auth, api)
        li_name_uri_list = printDict(li_dict, ['uri', 'name'])

        logging.info("Updating LI from group")
        for i, value in enumerate(li_name_uri_list):
            logging.info("Updating {} from LIG".format(li_name_uri_list[i]['name']))
            li_uri = li_name_uri_list[i]['uri']
            update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

        countdown(420)

        logging.info("Checking status of LE")
        GetStatusOfLogicalEnclosure(ip, auth, api)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        counter += 1
        countdown(30)


def testcase_remove_add_fc_network_li(auth, tor_ip, enc_name):
    logging.testcases("################################################")
    logging.testcases("TestCase: Remove/Add FC Network from ULS from LI")
    logging.testcases("################################################")

    testcase = 'Remove/Add FC Network from ULS from LI'
    counter = 0
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    retrieve_net_inst = Networks()
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()

    countdown(2)

    logging.info("Getting Fc network URIs")
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc2_bay1_uri, fc_net_enc2_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle28(
        ip, auth, api)
    logging.info("Getting Uplink sets URIs")
    uls_enc1_bay1_uri, uls_enc1_bay4_uri, uls_enc2_bay1_uri, uls_enc2_bay4_uri = retrieve_net_inst.get_uplink_set_uri_eagle28(
        ip, auth, api)

    logging.info("Getting Logical Interconnects")
    li_instance = LogicalInterconnects()
    li_dict = li_instance.GetLogicalInterconnects(ip, auth, api)
    li_name_uri_list = printDict(li_dict, ['uri', 'name'])
    for n, value in enumerate(li_name_uri_list):
        li_name = li_name_uri_list[n]['name']
        li_uri = li_name_uri_list[n]['uri']
        if li_name == "LE-LIG1-1":
            li_uri1 = li_uri
        elif li_name == "LE-LIG2-1":
            li_uri2 = li_uri
        elif li_name == "LE-LIG2-2":
            li_uri2 = li_uri

    uplink_sets_inst = AddRemoveUplinkSetsLiME()

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        uplink_sets_inst.RemoveUlsBay1FcNetworkLiEnc1(ip, auth, api, li_uri1, enc1_uri, uls_enc1_bay1_uri)
        logging.info("Removing FC network from BAY1-EAGLE28 uplink set")
        countdown(300)

        uplink_sets_inst.AddUlsBay1FcNetworkLiEnc1(ip, auth, api, fc_net_enc1_bay1_uri, li_uri1, enc1_uri,
                                                   uls_enc1_bay1_uri)
        logging.info("Adding FC network back to BAY1-EAGLE28 uplink set")
        countdown(420)

        logging.info("Checking state of carbons, status of UL and DL ports, and getting the number of FLOGIs")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


        uplink_sets_inst.RemoveUlsBay4FcNetworkLiEnc1(ip, auth, api, li_uri1, enc1_uri, uls_enc1_bay4_uri)
        logging.info("Removing FC network from BAY4-EAGLE28 uplink set")
        countdown(420)

        uplink_sets_inst.AddUlsBay4FcNetworkLiEnc1(ip, auth, api, fc_net_enc1_bay4_uri, li_uri1, enc1_uri,
                                                   uls_enc1_bay4_uri)
        logging.info("Adding FC network back to BAY4-EAGLE28 uplink set")
        countdown(420)

        logging.info("Checking state of carbons, status of UL and DL ports, and getting the number of FLOGIs")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


        uplink_sets_inst.RemoveUlsBay1FcNetworkLiEnc2(ip, auth, api, li_uri2, enc2_uri, uls_enc2_bay1_uri)
        logging.info("Removing FC network from BAY1-EAGLE29 uplink set")
        countdown(420)

        uplink_sets_inst.AddUlsBay1FcNetworkLiEnc2(ip, auth, api, fc_net_enc2_bay1_uri, li_uri2, enc2_uri,
                                                   uls_enc2_bay1_uri)
        logging.info("Adding FC network back to BAY1-EAGLE29 uplink set")
        countdown(420)

        logging.info("Checking state of carbons, status of UL and DL ports, and getting the number of FLOGIs")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        uplink_sets_inst.RemoveUlsBay4FcNetworkLiEnc2(ip, auth, api, li_uri2, enc2_uri, uls_enc2_bay4_uri)
        logging.info("Removing FC network from BAY4-EAGLE29 uplink set")
        countdown(420)

        uplink_sets_inst.AddUlsBay4FcNetworkLiEnc2(ip, auth, api, fc_net_enc2_bay4_uri, li_uri2, enc2_uri,
                                                   uls_enc2_bay4_uri)
        logging.info("Adding FC network back to BAY4-EAGLE29 uplink set")
        countdown(420)

        logging.info("Checking state of carbons, status of UL and DL ports, and getting the number of FLOGIs")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        counter += 1
        countdown(120)


def testcase_reset_carbon(auth, tor_ip, enc_name):
    """
    1) Perform a Reset carbon in bay4
    2) Wait 5 mins
    3) check if carbon is configured state, if ok, 
    4) move on to the next carbon in bay1 and repeat above steps.
    """
    # This test case resets carbon in bay4, waits 7 mins, checks state of carbon, then moves on to carbon in bay1
    logging.testcases("#####################################")
    logging.testcases("TestCase: Carbon Reset stress test")
    logging.testcases("#####################################")

    testcase = 'Carbon Reset stress test'
    counter = 0
    logging.info("Checking the status of the downlink and uplink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    carbon_reset_inst = PowerStateOfCarbon()
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()

    logging.info("Getting Interconnects")
    ic_inst = Interconnects()
    get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
    ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])

    countdown(5)

    # While loop to reset carbon ICMs
    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        # For loop to interate thru carbon bay4 and perform reset operation
        logging.info("Resetting the carbon ICMs in bay4")
        for ic, value in enumerate(ic_name_uri_list):
            icm_uri = ic_name_uri_list[ic]['uri']
            icm_name = ic_name_uri_list[ic]['name']
            name = ic_name_uri_list[ic]['enclosureName']
            if icm_name == "{}, interconnect 4".format(name):
                logging.info("Performing Reset operation on the carbon in {}".format(icm_name))
                carbon_reset_inst.ResetCarbon(ip, auth, api, icm_uri)
            else:
                pass

        countdown(900)
        logging.info("Checking to see the state of the carbon in bay4")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        # For loop to iterate thru carbon bay1 and power it off
        logging.info("Resetting the carbon ICMs in bay1")
        for ic, value in enumerate(ic_name_uri_list):
            icm_uri = ic_name_uri_list[ic]['uri']
            icm_name = ic_name_uri_list[ic]['name']
            name = ic_name_uri_list[ic]['enclosureName']
            if icm_name == "{}, interconnect 1".format(name):
                logging.info("Performing Reset operation on the carbon in {}".format(icm_name))
                carbon_reset_inst.ResetCarbon(ip, auth, api, icm_uri)
            else:
                pass

        countdown(900)
        logging.info("Checking to see the state of the carbon in bay4")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        counter += 1
        countdown(30)
        logging.info("Starting next iteration")

def testcase_carbon_hostname(auth):
    logging.testcases("########################################")
    logging.testcases("TestCase: Update/Reset carbon hostname")
    logging.testcases("########################################")
    logging.info("Getting Interconnects info")
    ic_inst = Interconnects()
    get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
    ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])
    logging.info("Resetting hostname on carbon in bay1 to default before running test")
    carbon_location = 'CN7516060B, interconnect 1'
    reset_hostname = ''
    for ic, value in enumerate(ic_name_uri_list):
        ic_uri = ic_name_uri_list[ic]['uri']
        ic_name = ic_name_uri_list[ic]['name']
        name = ic_name_uri_list[ic]['enclosureName']
        if ic_name == carbon_location:
            ic_inst.CarbonHostnameUpdate(ip, auth, api, ic_uri, reset_hostname)
            logging.info("pausing 20 secs before fetching carbon hostname")
            countdown(20)
            pretest_carbon_hn = ic_inst.getCarbonHostname(ip, auth, api, name, carbon_location)
            logging.info(pretest_carbon_hn)
        else:
            pass

    new_hostname = 'eagle28-bay1'
    ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])
    logging.info("Updating hostname on carbon in bay1")
    for ic, value in enumerate(ic_name_uri_list):
        ic_uri = ic_name_uri_list[ic]['uri']
        ic_name = ic_name_uri_list[ic]['name']
        name = ic_name_uri_list[ic]['enclosureName']
        if ic_name == carbon_location:
            ic_inst.CarbonHostnameUpdate(ip, auth, api, ic_uri, new_hostname)
            logging.info("pausing 20 secs before fetching carbon hostname")
            countdown(20)
            new_carbon_hn = ic_inst.getCarbonHostname(ip, auth, api, name, carbon_location)
            logging.info(new_carbon_hn)
        else:
            pass
     
    tc = "Change carbon hostname"
    if new_carbon_hn == new_hostname:
        result = "Pass"
        PassOrFail(result, tc)
    else:
        result = "Fail"
        PassOrFail(result, tc)
    
    logging.info("Resetting hostname on carbon in bay1 to default")
    for ic, value in enumerate(ic_name_uri_list):
        ic_uri = ic_name_uri_list[ic]['uri']
        ic_name = ic_name_uri_list[ic]['name']
        name = ic_name_uri_list[ic]['enclosureName']
        if ic_name == carbon_location:
            ic_inst.CarbonHostnameUpdate(ip, auth, api, ic_uri, reset_hostname)
            logging.info("pausing 20 secs before fetching carbon hostname")
            countdown(20)
            default_carbon_hn = ic_inst.getCarbonHostname(ip, auth, api, name, carbon_location)
            logging.info(default_carbon_hn)
        else:
            pass

    tc = "Reset carbon hostname to default"
    if default_carbon_hn == pretest_carbon_hn:
        result = "Pass"
        PassOrFail(result, tc)
    else:
        result = "Fail"
        PassOrFail(result, tc)

def testcase_carbon_connected_to(auth, enc_name):
    logging.testcases("#####################################")
    logging.testcases("TestCase: Carbon Neighbor switch WWN")
    logging.testcases("#####################################")
    logging.info("Inside function %s", sys._getframe().f_code.co_name)
    ic_inst = Interconnects()
    for name in enc_name:
        GetInterconnectList = ic_inst.GetInterconnectMultiEnc(ip, auth, api, name)
        ic_list = printDict(GetInterconnectList, ['model', 'ports', 'firmwareVersion'])
        logging.info("Getting a list of uplink ports that are online\n")
        for i in range(0, len(ic_list)):
            PortList = ic_list[i]['ports']
            model = ic_list[i]['model']
            fw_ver = ic_list[i]['firmwareVersion']
            if model == "Virtual Connect SE 16Gb FC Module for Synergy":
                for p in range(0, len(PortList)):
                    IcPortStatusReason = PortList[p]['portStatusReason']
                    portName = PortList[p]['portName']
                    PortType = PortList[p]['portType']
                    PortFcProp = PortList[p]['fcPortProperties']
                    if IcPortStatusReason == "LoggedIn" and PortType == "Uplink":
                        neighbor = PortFcProp['neighborInterconnectName']
                        tc = "Carbon fw: {}, Neighbor wwn for port {} is {}".format(fw_ver, portName, neighbor)
                        if fw_ver > '5.20.82':
                            if neighbor != None:
                                result = "Pass"
                                PassOrFail(result, tc)
                        elif fw_ver <= '5.20.82':
                            if neighbor == None:
                                result = "Pass"
                                PassOrFail(result, tc)
                        else:
                            pass


def testcase_appliance_backup_restore(auth, eagle, tor_ip, enc_name):
    logging.testcases("#################################################")
    logging.testcases("TestCase: Appliance Backup/Restore")
    logging.testcases("#################################################")
    testcase = 'Appliance Backup/Restore'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    get_num_flogi_inst = GetFLOGI()
    all_states_inst = CheckAllStatesOfCarbon()
    backup_restore_inst = ApplianceBackup()
    countdown(5)

    backup_restore_inst.create_appl_backup(ip, auth, api, eagle)
    logging.info("Creating appliance backup")
    countdown(120)
    logging.info("Retreiving appliance backup file uri")
    backup_file_dict = backup_restore_inst.GetApplianceBackup(ip, auth, api)
    backup_file_list = printDict(backup_file_dict, ['uri', 'downloadUri'])
    backup_filename = backup_file_list[0]['uri']
    download_filename = backup_file_list[0]['downloadUri']
    backup_restore_inst.download_backup(ip, auth, api, download_filename, eagle)
    logging.info("the backup filename to be used: {}" .format(backup_filename))
    logging.info("Restoring appliance from backup")
    backup_restore_inst.RestoreApplianceFromBackup(ip, auth, api, backup_filename)
    logging.info("waiting 45 mins to check restore status")
    countdown(2700)
    restore_status_dict = backup_restore_inst.GetApplianceRestoreStatus(ip, api)
    restore_status_list = printDict(restore_status_dict, ['status', 'progressStep', 'completedPhaseSteps', 'totalPhaseSteps', 'restorePhase'])
    for i, value in enumerate(restore_status_list):
        status = restore_status_list[i]['status']
    logging.info("restore status is: {}" .format(status))
    if status == 'SUCCEEDED':
        logging.info("Restore of appliance has completed")
    elif status == 'IN_PROGRESS':
        logging.info("Restore of appliance is in progress")
        count = 0
        while status == 'IN_PROGRESS':
            restore_status_dict = backup_restore_inst.GetApplianceRestoreStatus(ip, api)
            restore_status_list = printDict(restore_status_dict, ['status'])
            status = restore_status_list[i]['status']
            if status == 'SUCCEEDED':
                logging.info("Restore of appliance has completed")
                break
            else:
                count += 1
                if count == 3:
                    logging.info("There must something wrong, quiting script")
                    sys.exit(0)
                logging.info("Restore of appliance is in progress.  Waiting 5 mins and checking status again")
                countdown(300)

    login_inst = LoginCreds()
    auth = login_inst.LoginToken(ip, api, username, ov_pw)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)
    
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


def testcase_create_le_supportdump(auth, eagle, tor_ip, enc_name):
    logging.testcases("#################################################")
    logging.testcases("TestCase: Oneview LE Supportdump")
    logging.testcases("#################################################")
    testcase = 'Oneview LE Supportdump'
    encrypted = 'true'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    get_num_flogi_inst = GetFLOGI()
    all_states_inst = CheckAllStatesOfCarbon()
    countdown(5)

    logging.info("Creating LE Supportdump")
    le_inst = LogicalEnclosure()
    support_dump, file_name = le_inst.Create_le_support_dump(ip, auth, api, encrypted, eagle)
    logging.info("support dump path {}" .format(support_dump))
    logging.info("decrypting support dump file")
    subprocess.Popen('decrypt-support-dump.bat {} ' .format(support_dump))
    countdown(20)
    logging.info("Filename being passed to untar_supportdump function: {}" .format(file_name))
    untar_supportdump(file_name, eagle)
    
    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


def testcase_efuse_carbon_power_off(auth, tor_ip, enc_name):
    # This test case efuses carbon in bays1 and 4, waits 6 mins, then checks the if carbons are in error state, other than configured state,
    # then checks the status of the uplink and downlink ports.
    logging.testcases("#################################################")
    logging.testcases("TestCase: Carbon Efuse stress test with power off")
    logging.testcases("#################################################")
    testcase = 'Carbon Efuse stress test with power off'
    addr_type = "dhcp"
    counter = 0
    logging.info("Checking the status of the downlink and uplink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    # Create Instances of Classes used in this script
    check_carbon_inst = CheckStateOfCarbon()
    efuse = EfuseResource()
    all_states_inst = CheckAllStatesOfCarbon()
    get_cbn_addr_type_inst = GetCarbonAddressType()
    get_num_flogi_inst = GetFLOGI()
    
    logging.info("Getting Enclosures ")
    enc_inst = Enclosures()
    enc_dict = enc_inst.GetEnc(ip, auth, api)
    enc_uri_list = printDict(enc_dict, ['uri'])

    countdown(5)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        # For loop to iterate thru carbon bay1 and power it off
        ic_inst = Interconnects()
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnectMultiEnc(ip, auth, api, name)
            ic_name_uri_list = printDict(get_ic_dict, ['uri','name','model','state'])
            logging.info("Power off the carbon ICMs in bay1")
            for ic, value in enumerate(ic_name_uri_list):
                ic_uri = ic_name_uri_list[ic]['uri']
                ic_name = ic_name_uri_list[ic]['name']
                carbon_power_inst = PowerStateOfCarbon()
                if ic_name == "{}, interconnect 1".format(name):
                    logging.info("Powering off the carbon in {}".format(ic_name))
                    carbon_power_inst.PowerOffCarbon(ip, auth, api, ic_uri)
                else:
                    pass

        countdown(180)
        logging.info("Checking to see if carbons are actually turned off")
        tc = "Power turned off on carbon bay1"
        check_carbon_inst.IsCarbonTurnedOffBay1(ip, auth, api, enc_name)
        result = "Pass"
        PassOrFail(result, tc)

        logging.info("Checking to see if carbon in bay1 is in Maintenance State")
        tc = "Carbon in bay1 in Maintenance state"
        mainstate = check_carbon_inst.CheckCarbonMaintenanceStateBay1(ip, auth, api, enc_name)
        print(mainstate)
        if mainstate == "Maintenance":
            result = "Pass"
        else:
            result = "Fail"
        PassOrFail(result, tc)

        logging.info("Efusing carbon in Bay1")
        for i, value in enumerate(enc_uri_list):
            enc_uri = enc_uri_list[i]['uri']
            bay = "1"
            efuse.EfuseCarbon(ip, auth, api, enc_uri, bay)
            countdown(300)
        countdown(180)

        logging.info("Checking to see if carbons are actually turned on")
        tc = "Power turned on carbon bay1"
        check_carbon_inst.IsCarbonTurnedOnBay1(ip, auth, api, enc_name)
        result = "Pass"
        PassOrFail(result, tc)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        get_cbn_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type, enc_name)
        countdown(30)

        # For loop to interate thru carbon bay4 and power it off
        ic_inst = Interconnects()
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnectMultiEnc(ip, auth, api, name)
            ic_name_uri_list = printDict(get_ic_dict, ['uri','name','model','state'])
            logging.info("Power off the carbon ICMs in bay4")
            for ic, value in enumerate(ic_name_uri_list):
                ic_uri = ic_name_uri_list[ic]['uri']
                ic_name = ic_name_uri_list[ic]['name']
                carbon_power_inst = PowerStateOfCarbon()
                if ic_name == "{}, interconnect 4".format(name):
                    logging.info("Powering off the carbon in {}".format(ic_name))
                    carbon_power_inst.PowerOffCarbon(ip, auth, api, ic_uri)
                else:
                    pass

        countdown(180)
        logging.info("Checking to see if carbons are actually turned off")
        tc = "Power turned off on carbon bay4"
        check_carbon_inst.IsCarbonTurnedOffBay4(ip, auth, api, enc_name)
        result = "Pass"
        PassOrFail(result, tc)

        logging.info("Checking to see if carbon in bay4 is in Maintenance State")
        tc = "Carbon in bay4 in Maintenance state"
        mainstate = check_carbon_inst.CheckCarbonMaintenanceStateBay4(ip, auth, api, enc_name)
        if mainstate == "Maintenance":
            result = "Pass"
        else:
            result = "Fail"
        PassOrFail(result, tc)

        logging.info("Now will efuse carbon in bay4")
        logging.info("Efusing carbon in Bay4")
        for i, value in enumerate(enc_uri_list):
            enc_uri = enc_uri_list[i]['uri']
            bay = "4"
            print("executing function to efuse for bay4")
            efuse.EfuseCarbon(ip, auth, api, enc_uri, bay)
            countdown(300)
        countdown(180)

        logging.info("Checking to see if carbons are actually turned on")
        tc = "Power turned on carbon bay4"
        check_carbon_inst.IsCarbonTurnedOnBay4(ip, auth, api, enc_name)
        result = "Pass"
        PassOrFail(result, tc)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        get_cbn_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type, enc_name)
        counter += 1
        countdown(30)



def main():
    # This section starts the DD image install process
    eagle = get_eagle_enclosure_map(ip)
    #filename = get_filename()
    setup_logging_Enhanced(filename, eagle)
    set_https_proxies_houston()
    auth = get_auth_token()
    before_reimage = get_ov_build_version(ip, auth, api)
    composer_ver = GetComposerType(auth)
    #build = get_type_of_oneview_build()
    #build_release = get_oneview_build_release()
    dd_image_url = "http://ci-artifacts04.vse.rdlabs.hpecorp.net/omni/%s/DDImage/%s/" % (build_release, composer_ver)
    ddimage_links = get_ddimage_links(dd_image_url)
    if build == 'ToT':
        tot_image = retrieve_ToT_DDimages_impl(ddimage_links)
        logging.info("The length of the tot build is:  {}".format(len(tot_image)))
        logging.info("The tot image being installed: {}".format(tot_image))
        InstallImage.DockerInstallDDimage(docker_ip, user, docker_pw, dd_image_url, tot_image, yaml_file)
    elif build == 'PassBuild':
        pass_image = retrieve_Pass_DDimages_impl(ddimage_links)
        logging.info("The length of the pass build is:  {}".format(len(pass_image)))
        logging.info("The pass build image being installed: {}".format(pass_image))
        InstallImage.DockerInstallDDimage(docker_ip, user, docker_pw, dd_image_url, pass_image, yaml_file)
    #THIS SECTION OF CODE CHECKS IF THE ONEVIEW UPDATE WAS SUCCESSFUL
    clear_https_proxies()
    auth = get_auth_token()
    after_reimage = get_ov_build_version(ip, auth, api)
    oneview_upgrade_check(before_reimage, after_reimage)
    #THIS SECTION OF CODE INITIALIZES LOGGING, RETRIEVES THE IP ADDRESS FOR THE TOR, AND RETRIEVES FIRMWARE VERSIONS FOR THE INSTALLED ICMS
    tor_ip = get_tor_ip(ip)
    auth = get_new_auth_token()
    get_enc_name_list = Enclosures()
    enc_name = get_enc_name_list.get_enclosure_name(ip, auth, api)
    get_ov_build_carbon_fw_version(auth, enc_name)
    #THIS SECTION OF CODE CONFIGURES EAGLE28
    create_fc_networks(auth)
    ic_types_name_uri = interconnect_type_uri(auth)
    create_carbon_lig(auth, ic_types_name_uri)
    lig1_uri, lig2_uri = get_lig_uri(auth)
    create_enclosure_group(auth, lig1_uri, lig2_uri)
    enc_grp_uri = get_enclosure_enc_group_uri(auth)
    create_le(auth, enc_grp_uri)
    check_le_status(auth)
    create_server_profiles(auth, eagle, enc_grp_uri)
    check_sp_status(auth)
    preflight_check(auth, tor_ip, enc_name)
    #THIS SECTION OF CODE STARTS THE REGRESSION TESTCASES
    testcase_power_off_on_carbon(auth, tor_ip, enc_name)
    testcase_efuse_carbon(auth, tor_ip, enc_name)
    testcase_efuse_carbon_power_off(auth, tor_ip, enc_name)
    testcase_reset_carbon(auth, tor_ip, enc_name)
    testcase_restart_oneview(auth, tor_ip, enc_name)
    testcase_icm_utilization(auth, enc_name)
    testcase_remote_syslog(auth, enc_name)
    testcase_connectorinfo_digitaldiag(auth)
    testcase_staticIp_add_remove_encgrp(auth, tor_ip, enc_name)
    testcase_aside_bside_ligs(auth, tor_ip, enc_name)
    testcase_add_remove_lig_enclosure_group(auth, tor_ip, enc_name)
    testcase_change_port_speeds_tor(auth, tor_ip, enc_name)
    testcase_disable_enable_trunking_lig(auth, tor_ip, enc_name)
    testcase_remove_add_fc_network_li(auth, tor_ip, enc_name)
    testcase_remove_add_fcnetwork_lig(auth, tor_ip, enc_name)
    testcase_update_sp_speeds(auth, tor_ip, enc_name)
    testcase_carbon_hostname(auth)
    testcase_carbon_connected_to(auth, enc_name)
    testcase_create_le_supportdump(auth, eagle, tor_ip, enc_name)
    testcase_appliance_backup_restore(auth, eagle, tor_ip, enc_name)


if __name__ == '__main__':
    main()
