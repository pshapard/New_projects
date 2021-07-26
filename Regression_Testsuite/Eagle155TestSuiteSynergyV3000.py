"""
/usr/bin/python
Author: Patrick Shapard @HPE,
created: 04/22/2021
updated: 05/20/2021
This script automates the execution of the following test cases for Synergy enclosure with carbons installed on Eagle155


TestCase: Upload signed certificate(multiple iterations)
TestCase: Carbon Failover stress test(multiple iterations)
TestCase: Efuse Carbon Stress Test (multiple iterations)
TestCase: Carbon Reset stress test
TestCase: Remove/Add FC Network from ULS from LIG (multiple iterations)
TestCase: Remove/Add FC Network from ULS from LI (multiple iterations)
TestCase: Server Profile FC Connection set to 32GB/16GB/Auto
TestCase: Carbon Utilization Samples
TestCase: Enable/Disable RemoteSyslog Ipv4 and Ipv6
TestCase: Connector Information and Digital Diagnostics
TestCase: Add/Remove IPv4 Static Address Range to/from Enclosure Group
TestCase: Restart of Oneview (multiple iterations)
TestCase: UFG LE with A-Side B-side LIGs (multiple iterations)
TestCase: Configure Port Monitor, Bi-directional, To Server, From Server
TestCase: Change port speeds(8/16/32GB) on ToR FC switch
TestCase: Remove/Add LIG from/to Enclosure Group
TestCase: Redistribution Logins; Auto and Manual
TestCase: Oneview LE Supportdump(encrypted)
TestCase: Appliance Backup/Restore

These testcases need to be developeed for eagle155
TestCase: Disable/Enable Trunking on LIG
TestCase: Speed set to 4Gb/8Gb/16Gb with Trunking Enabled in LIG
TestCase: LIG Port speed change stress test
"""

import json
import logging
import subprocess
import sys

from SynergyV3000 import AddRemoveUplinkSetsLi
from SynergyV3000 import ApplianceBackup
from SynergyV3000 import ApplianceSettings
from SynergyV3000 import Certificates
from SynergyV3000 import CheckAllStatesOfCarbon
from SynergyV3000 import CheckStateOfCarbon
from SynergyV3000 import ConfigureTOR
from SynergyV3000 import ConnectorDigDiagInfo
from SynergyV3000 import CreateEnclosureGroup
from SynergyV3000 import CreateFibreChannelNetworks
from SynergyV3000 import CreateLogicalEnclosure
from SynergyV3000 import CreateLogicalInterconnectGroup
from SynergyV3000 import EfuseResource
from SynergyV3000 import Enclosures
from SynergyV3000 import GetCarbonAddressType
from SynergyV3000 import GetCarbonDownLinkPorts  # function
from SynergyV3000 import GetCarbonPortStatus
from SynergyV3000 import GetCarbonUpLinkPorts  # function
from SynergyV3000 import GetFLOGI
from SynergyV3000 import GetSPStatus  # function
from SynergyV3000 import GetStatusOfLogicalEnclosure  # function
from SynergyV3000 import Interconnects
from SynergyV3000 import LogicalEnclosure
from SynergyV3000 import LogicalInterconnectGroup
from SynergyV3000 import LogicalInterconnects
from SynergyV3000 import LoginCreds
from SynergyV3000 import Networks
from SynergyV3000 import OneViewBuildVersion
from SynergyV3000 import PassOrFail  # function
from SynergyV3000 import PortMonitor
from SynergyV3000 import PowerOffOnServers
from SynergyV3000 import PowerStateOfCarbon
from SynergyV3000 import RemoteSyslog
from SynergyV3000 import ServerProfileBfsLunsNewDTO
from SynergyV3000 import ServerProfileConnectionSpeeds
from SynergyV3000 import Servers
from SynergyV3000 import StateOfEnclosure
from SynergyV3000 import UpdateEnclosureGroup as UpdateEG
from SynergyV3000 import UpdateLogicalEnclosure
from SynergyV3000 import UpdateLogicalInterconnectGroup
from SynergyV3000 import UpdateLogicalInterconnects
from SynergyV3000 import UpdateNetworks
from SynergyV3000 import UpdateServerProfileBfsLunsNewDTO
from SynergyV3000 import api, username, ov_pw, tor_pw, tor_un
from SynergyV3000 import countdown  # function
from SynergyV3000 import determine_num_iterations  # function
from SynergyV3000 import get_eagle_enclosure_map
from SynergyV3000 import get_task
from SynergyV3000 import get_tor_ip
from SynergyV3000 import printDict  # function
from SynergyV3000 import setup_logging_Enhanced
from SynergyV3000 import untar_supportdump  # function
from requests.exceptions import ConnectionError

ip = "15.186.9.155"
# Initialize logging function with enhancements
filename = 'TestSuiteSynergyV3000_5.40.113'
# Global Variable
fc_mode = "TRUNK"
v3_enabled = "true"
consistency_check = "ExactMatch"
lig_name = "LIG"
enc_uri = '/rest/enclosures/797739MXQ81306V8'
number = 1


"""
please note, certificate test case need login creds hidden
"""


def get_auth_token():
    login_inst = LoginCreds()
    try:
        auth = login_inst.LoginToken(ip, api, username, ov_pw)
    except ConnectionError as e:
        logging.info("Could not connect to host")
        # logging.info("{}" .format(e))
        sys.exit(0)
    return auth


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
    fibre_chanel_network = ('BAY1', 'BAY4', 'BAY1-Q1-PORTS')
    for net in fibre_chanel_network:
        logging.info("Creating {} network".format(net))
        fc_net_inst = CreateFibreChannelNetworks()
        fc_net_inst.CreateFcNetwork(ip, auth, api, net)


def get_enclosure_uri(auth):
    logging.info("Getting Enclosures ")
    enc_inst = Enclosures()
    enc_dict = enc_inst.GetEnc(ip, auth, api)
    enclosure_uri = printDict(enc_dict, ['uri'])
    enc_uri = enclosure_uri[0]['uri']
    return enc_uri


def interconnect_type_uri(auth):
    logging.info("Getting interconnect types uri")
    ic_inst = Interconnects()
    ic_types = ic_inst.GetInterconnectTypes(ip, auth, api)
    ic_types_name_uri = printDict(ic_types, ['name', 'uri'])
    return ic_types_name_uri


def create_lig(auth, ic_types_name_uri):
    retrieve_net_inst = Networks()
    create_lig_inst = CreateLogicalInterconnectGroup()
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle21(
        ip, auth, api)
    logging.info("Creating a LIG")
    for s, value in enumerate(ic_types_name_uri):
        ic_type_uri = ic_types_name_uri[s]['uri']
        ic_name = ic_types_name_uri[s]['name']
        if ic_name == "Virtual Connect SE 32Gb FC Module for Synergy":
            create_lig_inst.CreateLigE155(ip, auth, api, lig_name, ic_type_uri, fc_net_enc1_bay1_uri,
                                          fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, fc_mode, v3_enabled,
                                          consistency_check)
    logging.info('Pausing for 30 secs for LIGs to be created')
    countdown(0, 30)


def get_lig_uri(auth):
    ligs_inst = LogicalInterconnectGroup()
    ligs_list = ligs_inst.GetListOfLIGs(ip, auth, api)
    lig_uri = printDict(ligs_list, ['uri'])
    lig_uri = lig_uri[0]['uri']
    return lig_uri


def create_enclosure_group(auth, lig_uri):
    create_eg_inst = CreateEnclosureGroup()
    create_eg_inst.CreateEgTBird(ip, auth, api, lig_uri)
    logging.info('Pausing for 30 secs for EG to be created')
    countdown(0, 30)


def get_eg_uri(auth):
    logging.info("Getting Enclosure Group")
    enc_inst = Enclosures()
    enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
    encl_group_uri_dict = printDict(enc_grp_dict, ['uri'])
    enc_grp_uri = encl_group_uri_dict[0]['uri']
    return enc_grp_uri


def create_le(auth, enc_grp_uri):
    logging.info("Creating Logical Enclosure")
    create_log_enc_inst = CreateLogicalEnclosure()
    create_log_enc_inst.CreateLE(ip, auth, api, enc_uri, enc_grp_uri)
    logging.info('Pausing for 8 mins.  Waiting for LE to be created')
    countdown(8, 0)


def check_le_status(auth):
    logging.info('Checking status of LE')
    GetStatusOfLogicalEnclosure(ip, auth, api)


def create_server_profiles(auth, eagle, enc_grp_uri):
    retrieve_net_inst = Networks()
    power_cycle_server_inst = PowerOffOnServers()
    create_sp_inst = ServerProfileBfsLunsNewDTO()
    server_hw_profiles = Servers()
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle21(
        ip, auth, api)
    array_wwpn1, array_wwpn2, wwnn1_start, wwpn1_start, wwnn2_start, wwpn2_start = server_hw_profiles.server_wwnn_start_wwpn_start(
        eagle)
    sp_name, sp_descr, id_1, id_2 = server_hw_profiles.server_profile_config()
    logging.info("Getting Server HW and Profiles")
    server_hw_list = server_hw_profiles.ServerHW(ip, auth, api)
    server_hw_names_dict = printDict(server_hw_list, ['name', 'uri', 'model', 'serialNumber'])
    shw_dict_sorted = sorted(server_hw_names_dict)
    power_cycle_server_inst.power_off_servers(ip, auth, api)
    mode = "UEFI"

    logging.info("starting Server HW list loop to create server profiles")
    for i, value in enumerate(shw_dict_sorted):
        server_hw_uri = shw_dict_sorted[i]['uri']
        server_name = shw_dict_sorted[i]['name']
        server_sn = shw_dict_sorted[i]['serialNumber']
        logging.info("Creating {} for server {} sn {}".format(sp_name[i], server_name, server_sn))
        if server_sn == "MXQ94701Y8":
            wwpn1 = '10:00:70:10:6f:76:b5:84'
            wwnn1 = '20:00:70:10:6f:76:b5:84'
            wwpn2 = '10:00:70:10:6f:76:b5:85'
            wwnn2 = '20:00:70:10:6f:76:b5:85'
            create_sp_inst.CreateServerProfileLuns(ip, auth, api, sp_name[i], server_hw_uri, enc_grp_uri, sp_descr[i],
                                                   fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1,
                                                   wwpn1, wwnn2, wwpn2, mode)
        elif server_sn == "MXQ82104C6":
            wwpn1 = '10:00:70:10:6f:76:b5:80'
            wwnn1 = '20:00:70:10:6f:76:b5:80'
            wwpn2 = '10:00:70:10:6f:76:b5:81'
            wwnn2 = '20:00:70:10:6f:76:b5:81'
            create_sp_inst.CreateServerProfileLuns(ip, auth, api, sp_name[i], server_hw_uri, enc_grp_uri, sp_descr[i],
                                                   fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1,
                                                   wwpn1, wwnn2, wwpn2, mode)
        elif server_sn == "MXQ72407GR":
            wwpn1 = '10:00:70:10:6f:76:b5:86'
            wwnn1 = '20:00:70:10:6f:76:b5:86'
            wwpn2 = '10:00:70:10:6f:76:b5:87'
            wwnn2 = '20:00:70:10:6f:76:b5:87'
            create_sp_inst.CreateServerProfileLuns(ip, auth, api, sp_name[i], server_hw_uri, enc_grp_uri, sp_descr[i],
                                                   fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1,
                                                   wwpn1, wwnn2, wwpn2, mode)
        elif server_sn == "MXQ832018F":
            wwpn1 = '10:00:70:10:6f:76:b5:82'
            wwnn1 = '20:00:70:10:6f:76:b5:82'
            wwpn2 = '10:00:70:10:6f:76:b5:83'
            wwnn2 = '20:00:70:10:6f:76:b5:83'
            create_sp_inst.CreateServerProfileBootFromSAN(ip, auth, api, sp_name[i], server_hw_uri, enc_grp_uri,
                                                          sp_descr[i], fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri,
                                                          id_1[i], id_2[i], wwnn1, wwpn1, array_wwpn1, wwnn2, wwpn2,
                                                          array_wwpn2, mode)
        else:
            pass

    logging.info("*******************POWERING ON SERVERS **********************************")
    logging.info("Pausing 7m30s for server profiles to be created before powering on the servers")
    countdown(7, 30)


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
    countdown(7, 0)
    power_cycle_server_inst.check_server_power(ip, auth, api)


def preflight_check(auth, tor_ip, enc_name):
    logging.info("Checking state of carbons before starting testsuite")
    check_carbon_inst = CheckStateOfCarbon()
    check_carbon_inst.CheckCarbonForErrors(ip, auth, api, enc_name)
    check_carbon_inst.CheckCarbonState(ip, auth, api, enc_name)
    get_num_flogi = GetFLOGI()
    get_num_flogi.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)


##################################REGRESSION TESTSUITE STARTS HERE####################################################################################

def get_icm_uri(auth):
    logging.info("Getting Interconnects")
    ic_inst = Interconnects()
    get_ic_list = ic_inst.GetInterconnect(ip, auth, api)
    ic_list = printDict(get_ic_list, ['name', 'uri', 'model', 'enclosureName'])

    for ic, value in enumerate(ic_list):
        ic_uri = ic_list[ic]['uri']
        ic_name = ic_list[ic]['name']
        enc_name = ic_list[ic]['enclosureName']
        if ic_name == "{}, interconnect 4".format(enc_name):
            logging.info("Retrieving the URI for carbon in {}".format(ic_name))
            return ic_uri
        else:
            pass


def testcase_upload_signed_certs(auth, icm_uri, tor_ip, enc_name):
    logging.testcases("############################################")
    logging.testcases("TestCase: Carbon32 Upload signed certificate")
    logging.testcases("############################################")
    testcase = "Carbon32 Upload Signed Certificates"
    ou = 'bay4-eagle155.hpe.com'
    snmp_server_ip = '15.186.27.149'
    user = 'root'
    tor_un = 'admin'
    passwd = 'password@123'
    tor_pw = 'hpvse123'
    cnf_file = 'openssl.cnf_eagle155'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    # Create Instance of Classes used in this script
    cert_inst = Certificates()
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()

    logging.info("Creating CSR")
    cert_inst.create_csr(ip, auth, api, icm_uri, ou)
    countdown(1, 30)
    print "retrieving CSR"
    logging.info("Creating CSR")
    bay_cert_request = cert_inst.retrieve_csr(ip, auth, icm_uri)
    csr = bay_cert_request['base64Data']
    logging.info("Writing to CSR to file")
    cert_inst.write_csr_to_file(csr)
    logging.info("Copying CSR to cert server")
    cert_inst.copy_csr_file_snmp_server(snmp_server_ip, user, passwd)
    logging.info("Deleting and create index file")
    cert_inst.delete_create_index_file(snmp_server_ip, user, passwd)
    logging.info("signing bay4 cert")
    cert_inst.sign_bay4_cert(snmp_server_ip, user, passwd, cnf_file)
    logging.info("Combining ca chain and signed bay4 cert")
    bay4_signed_cert_string = cert_inst.combine_ca_chain_carbon_signed_cert(snmp_server_ip, user, passwd)
    bay4_signed_cert_dump = json.dumps(bay4_signed_cert_string)
    countdown(2, 0)
    cert_inst.upload_signed_certificate(ip, auth, api, icm_uri, bay4_signed_cert_dump)
    # cert_inst.delete_signed_cert_file(snmp_server_ip, user, passwd)
    countdown(1, 0)
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


def testcase_remove_add_fcnetwork_lig(auth, tor_ip, enc_name):
    """"
    Steps for add/remove FC network from LIG
    1) Remove fc network from ULS from bay1 from LIG, wait 15 secs
    2) Run update from group, wait 10 mins
    3) Add fc network back to ULS bay1, wait 15 secs
    4) Run update from group from LI, wait 7 mins
    5) check state of carbon and status of UL and DL ports, any failure detected, script will stop
    6) Remove fc network from ULS from bay4 from LIG, wait 15 secs
    7) Run update from group, wait 10 mins
    8) Add fc network back to ULS bay4, wait 15 secs
    9) Run update from group from LI, wait 7 mins
    10) check state of carbon and status of UL and DL ports, any failure detected, script will stop
    """
    logging.testcases("#################################################")
    logging.testcases("TestCase: Remove/Add FC Network from ULS from LIG")
    logging.testcases("#################################################")
    testcase = "Remove/Add FC Network from ULS from LIG"
    fc_mode = "TRUNK"
    v3_enabled = "true"
    tor_pw = 'hpvse123'
    counter = 0
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    # Create Instance of Classes used in this script
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()
    retrieve_net_inst = Networks()
    countdown(0, 2)

    logging.info("Getting interconnect types uri")
    ic_types_inst = Interconnects()
    ic_types_list = ic_types_inst.GetInterconnectTypes(ip, auth, api)
    ic_types_name_uri = printDict(ic_types_list, ['uri', 'name'])

    logging.info("Getting Fc network URIs")
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle21(
        ip, auth, api)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Getting list of LIGs")
        ligs_inst = LogicalInterconnectGroup()
        ligs_list = ligs_inst.GetListOfLIGs(ip, auth, api)
        ligs_name_uri = printDict(ligs_list, ['name', 'uri'])
        lig_uri = ligs_name_uri[0]['uri']
        for i in range(0, len(ligs_name_uri)):
            lig_name = ligs_name_uri[i]['name']
            if lig_name == "LIG":
                lig_uri = ligs_name_uri[i]['uri']
        for s in range(0, len(ic_types_name_uri)):
            ic_type_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 32Gb FC Module for Synergy":
                add_remove_network = UpdateLogicalInterconnectGroup()
                add_remove_network.update_lig_no_network_bay1_eagle155(ip, auth, api, ic_type_uri, lig_uri, fc_mode,
                                                                       v3_enabled, fc_net_enc1_bay4_uri,
                                                                       fc_net_enc1_bay1_quri, consistency_check)

        countdown(0, 15)
        logging.info("Getting Logical Interconnects")
        li_inst = LogicalInterconnects()
        li_list = li_inst.GetLogicalInterconnects(ip, auth, api)
        li_name_uri = printDict(li_list, ['uri', 'name'])

        logging.info("Updating LI from group")
        for i in range(0, len(li_name_uri)):
            logging.info("Updating {} from LIG".format(li_name_uri[i]['name']))
            li_uri = li_name_uri[i]['uri']
            update_li_inst = UpdateLogicalInterconnects()
            update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

        countdown(7, 0)

        for s in range(0, len(ic_types_name_uri)):
            ic_type_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 32Gb FC Module for Synergy":
                add_remove_network.update_lig_both_networks_eagle155(ip, auth, api, ic_type_uri, lig_uri, fc_mode,
                                                                     v3_enabled, fc_net_enc1_bay1_uri,
                                                                     fc_net_enc1_bay4_uri, fc_net_enc1_bay1_quri,
                                                                     consistency_check)

        countdown(0, 15)

        logging.info("Updating LI from group")
        for i in range(0, len(li_name_uri)):
            logging.info("Updating {} from LIG".format(li_name_uri[i]['name']))
            li_uri = li_name_uri[i]['uri']
            update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)
            logging.info("Pausing for 3mins before checking state and downlink ports on carbons\n")

        countdown(7, 0)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        for s in range(0, len(ic_types_name_uri)):
            ic_type_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 32Gb FC Module for Synergy":
                add_remove_network.update_lig_no_network_bay4_eagle155(ip, auth, api, ic_type_uri, lig_uri, fc_mode,
                                                                       v3_enabled, fc_net_enc1_bay1_uri,
                                                                       fc_net_enc1_bay1_quri, consistency_check)

        countdown(0, 30)
        logging.info("Updating LI from group")
        for i in range(0, len(li_name_uri)):
            logging.info("Updating {} from LIG".format(li_name_uri[i]['name']))
            li_uri = li_name_uri[i]['uri']
            update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

        countdown(7, 0)
        for s in range(0, len(ic_types_name_uri)):
            ic_type_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 32Gb FC Module for Synergy":
                add_remove_network.update_lig_both_networks_eagle155(ip, auth, api, ic_type_uri, lig_uri, fc_mode,
                                                                     v3_enabled, fc_net_enc1_bay1_uri,
                                                                     fc_net_enc1_bay4_uri, fc_net_enc1_bay1_quri,
                                                                     consistency_check)

        countdown(0, 30)
        logging.info("Getting Logical Interconnects")
        li_list = li_inst.GetLogicalInterconnects(ip, auth, api)
        li_name_uri = printDict(li_list, ['uri', 'name'])

        logging.info("Updating LI from group")
        for i in range(0, len(li_name_uri)):
            logging.info("Updating {} from LIG".format(li_name_uri[i]['name']))
            li_uri = li_name_uri[i]['uri']
            update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

        countdown(7, 0)
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        counter += 1
        countdown(0, 10)

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

    countdown(0, 5)

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
    
        countdown(2, 0)
        logging.info("Checking to see if carbons are actually turned off")
        tc = "Power turned off on carbon bay4"
        check_carbon_inst.IsCarbonTurnedOffBay4(ip, auth, api, enc_name)
        result = "Pass"
        PassOrFail(result, tc)
        logging.info("Waiting 3 minutes before powering on carbons in bay4.")
        countdown(3, 0)
    
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
                    countdown(4, 0)
                else:
                    pass
    
        countdown(7, 0)
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
    
        countdown(2, 0)
        logging.info("Checking to see if carbons are actually turned off")
        tc = "Power turned off on carbon bay1"
        check_carbon_inst.IsCarbonTurnedOffBay1(ip, auth, api, enc_name)
        result = "Pass"
        PassOrFail(result, tc)
        logging.info("Waiting 3 minutes before powering on carbons in bay1.")
        countdown(3, 0)
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
                    countdown(4, 0)
                else:
                    pass
        
        countdown(7, 0)
    
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        counter += 1
        countdown(0, 30)
        logging.info("Starting next iteration")

def testcase_efuse_carbon(auth, tor_ip, enc_name):
    """
    1) Efuse carbon in bay1 for each enclosure
    2) wait 6 mins for each efuse operation on each carbon
    3) Flogi validation
    4) UL, DL, and carbon state validation
    5) ip address type validation
    6) Efuse carbon in bay4 for each enclosure
    7) wait 6 mins for each efuse operation on each carbon
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

    countdown(0, 5)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Efusing carbon(s) in Bay1")
        for i, value in enumerate(enc_uri_list):
            enc_uri = enc_uri_list[i]['uri']
            bay = "1"
            efuse_inst.EfuseCarbon(ip, auth, api, enc_uri, bay)
            countdown(5, 0)
        countdown(1, 0)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        get_cbn_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type, enc_name)

        countdown(0, 30)
        logging.info("Pausing 30secs before moving on to bay4")
        logging.info("Efusing carbon in Bay4")
        for i, value in enumerate(enc_uri_list):
            enc_uri = enc_uri_list[i]['uri']
            bay = "4"
            print "executing function to efuse for bay4"
            efuse_inst.EfuseCarbon(ip, auth, api, enc_uri, bay)
            countdown(5, 0)
        countdown(1, 0)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        get_cbn_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type, enc_name)
        counter += 1
        countdown(0, 30)



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
        countdown(45, 0)

        login = LoginCreds()
        auth = login.LoginToken(ip, api, username, ov_pw)

        refresh_state = state_of_enc_inst.EncRefreshState(ip, auth, api)

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
    countdown(0, 5)

    tc = "Enable RemoteSyslog Ipv6"
    remote_syslog_inst = RemoteSyslog()

    logging.info("Enable remote Syslog with IPv6 address")
    remote_syslog_inst.EnableRemoteSyslogIPv6(ip, auth, api)
    countdown(3, 0)
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

    countdown(0, 15)
    tc = "Disable RemoteSyslog Ipv6"
    logging.info("Disable remote Syslog with IPv6 address")
    remote_syslog_inst.DisableRemoteSyslogIPv6(ip, auth, api)
    countdown(3, 0)
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
    countdown(3, 0)
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

    countdown(0, 15)

    logging.info("Disable remote Syslog with IPv4 address\n")
    tc = "Disable RemoteSyslog Ipv4"
    remote_syslog_inst.DisableRemoteSyslogIPv4(ip, auth, api)
    countdown(3, 0)
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
    enc_inst = Enclosures()
    enc_dict = enc_inst.GetEnc(ip, auth, api)
    enc_name_list = printDict(enc_dict, ['name'])
    for x, value in enumerate(enc_name_list):
        enc_name = enc_name_list[x]['name']
        logging.info("Getting Interconnects")
        interconnect_dict = Interconnects()
        get_interconnect_list = interconnect_dict.GetInterconnectMultiEnc(ip, auth, api, enc_name)
        ic_model_list = printDict(get_interconnect_list, ['model', 'name', 'uri'])
        ic_model_list_sorted = sorted(ic_model_list)
        for ic, value in enumerate(ic_model_list_sorted):
            ic_uri = ic_model_list_sorted[ic]['uri']
            ic_name = ic_model_list_sorted[ic]['name']
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
    logging.testcases("######################################################################")
    logging.testcases("TestCase: Add/Remove IPv4 Static Address Range to/from Enclosure Group")
    logging.testcases("######################################################################")
    network_id = '192.168.1.0'
    gateway = '192.168.1.1'
    start_address = '192.168.1.10'
    end_address = '192.168.1.254'
    testcase = 'Add/Remove IPv4 Static Address Range to/from Enclosure Group'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    countdown(0, 5)

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
    lig_list = ligs_inst.GetListOfLIGs(ip, auth, api)
    lig_names = printDict(lig_list, ['name'])
    lig_uri_list = printDict(lig_list, ['uri'])

    update_enc_grp_inst = UpdateEG()

    for i, value in enumerate(lig_names):
        lig_name = lig_names[i]['name']
        if lig_name == "LIG":
            lig1_uri = lig_uri_list[i]['uri']

    logging.info("Creating IPv4 subnet ")
    ipv4_settings.CreateIPv4Subnet(ip, auth, api, network_id, gateway)
    logging.info("Getting ipv4 subnet")
    get_subnet = ipv4_settings.GetIPv4Subnet(ip, auth, api)
    subnet_list = printDict(get_subnet, ['uri', 'networkId'])
    networkid = [x for x in subnet_list if x['networkId'] == network_id]
    subnet_uri = networkid[0]['uri']
    logging.info("Creating ipv4 address range")
    ipv4_settings.CreateIPv4Range(ip, auth, api, start_address, end_address, subnet_uri)
    countdown(0, 2)
    get_network = ipv4_settings.GetIPv4Subnet(ip, auth, api)
    ipv4_range = printDict(get_network, ['rangeUris', 'networkId'])
    network_range = [x for x in ipv4_range if x['networkId'] == network_id]
    range_uri_list = network_range[0]['rangeUris']
    range_uri = range_uri_list[0]
    logging.info("Updating Enclosure Group with Static IPv4 address range")
    update_enc_grp_inst.UpdateEGIPv4RangeE21(ip, auth, api, enc_grp_uri, enc_grp_etag, range_uri, lig1_uri)

    countdown(0, 30)
    logging.info("*******************UPDATING LE ***************************")

    logging.info("Getting Logical Enclosure")
    le_inst = LogicalEnclosure()
    le_dict = le_inst.GetLogicalEnclosure(ip, auth, api)
    le_uri_list = printDict(le_dict, ['uri'])
    le_uri = le_uri_list[0]['uri']

    logging.info("Updating LE from group")
    update_le = UpdateLogicalEnclosure()
    update_le.LeUpdateFromGroup(ip, auth, api, le_uri)

    logging.info("Pausing for 15mins to wait for the LE to updated from group")
    countdown(15, 0)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    addr_type = 'static'
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
    get_cbn_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type, enc_name)

    countdown(0, 30)
    logging.info("*******************RESETTING EG TO DEFAULT VALUES ***************************")

    logging.info("Getting list of LIGs")
    ligs_inst = LogicalInterconnectGroup()
    lig_list = ligs_inst.GetListOfLIGs(ip, auth, api)
    lig_names = printDict(lig_list, ['name'])
    lig_uri_list = printDict(lig_list, ['uri'])

    logging.info("Getting Enclosure Group ")
    enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
    enc_grp_list = printDict(enc_grp_dict, ['name', 'uri', 'eTag'])
    enc_grp_uri = enc_grp_list[0]['uri']
    enc_grp_etag = enc_grp_list[0]['eTag']

    for i, value in enumerate(lig_names):
        lig_name = lig_names[i]['name']
        if lig_name == "LIG":
            lig1_uri = lig_uri_list[i]['uri']

    update_enc_grp_inst.UpdateEgDefaultE21(ip, auth, api, enc_grp_uri, enc_grp_etag, lig1_uri)
    logging.info("Pausing for 30 secs for EG to be created")
    countdown(0, 20)

    logging.info("Updating LE from group")
    update_le.LeUpdateFromGroup(ip, auth, api, le_uri)

    logging.info("********************UPDATE FROM GROUP THE LE***************************")
    logging.info("Pausing for 10mins for LE to be updated from group")
    countdown(10, 0)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    addr_type = 'dhcp'
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
    get_cbn_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type, enc_name)


def testcase_update_sp_speeds(auth, eagle, tor_ip, enc_name):
    logging.testcases("#############################################################")
    logging.testcases("TestCase: Server Profile FC Connection set to 32GB/16GB/Auto")
    logging.testcases("#############################################################")
    testcase = 'Server Profile FC Connection set to 32GB/16GB/Auto'
    counter = 0
    tor_pw = 'hpvse123'

    logging.info("Checking the status of the uplinks ports and downlink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    countdown(0, 5)

    sp_speeds = ServerProfileConnectionSpeeds()
    update_sp_inst = UpdateServerProfileBfsLunsNewDTO()
    all_states_carbon = CheckAllStatesOfCarbon()
    power_cycle_server_inst = PowerOffOnServers()
    retrieve_net_inst = Networks()
    get_num_flogi_inst = GetFLOGI()

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Getting Fc network URIs")
        fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle21(
            ip, auth, api)

        logging.info("*******************POWERING OFF SERVERS *************************************")
        power_cycle_server_inst.power_off_servers(ip, auth, api)

        logging.info("Getting Enclosure Group ")
        enc_inst = Enclosures()
        enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
        enc_grp_name_uri = printDict(enc_grp_dict, ['name', 'uri'])
        enc_grp_uri = enc_grp_name_uri[0]['uri']

        logging.info("Getting Server HW and Profiles")
        server_hw_profiles = Servers()
        array_wwpn1, array_wwpn2, wwnn1_start, wwpn1_start, wwnn2_start, wwpn2_start = server_hw_profiles.server_wwnn_start_wwpn_start(
            eagle)
        sp_name, sp_descr, id_1, id_2 = server_hw_profiles.server_profile_config()
        wwnn1, wwpn1, wwnn2, wwpn2 = server_hw_profiles.server_wwwn_wwpn(wwnn1_start, wwpn1_start, wwnn2_start,
                                                                         wwpn2_start)
        sp_dict = server_hw_profiles.ServerProfiles(ip, auth, api)
        sp_list = printDict(sp_dict,
                            ['name', 'uri', 'state', 'serverHardwareUri', 'enclosureBay', 'eTag', 'connectionSettings'])
        sp_list_sorted = sorted(sp_list)

        logging.info("*******************UPDATING FC CONNECTIONS TO 32GB***************************")

        requested_bw = "32000"
        mode = "UEFI"

        logging.info("Starting Server Profile list loop")
        for i, value in enumerate(sp_list_sorted):
            server_hw_uri = sp_list_sorted[i]['serverHardwareUri']
            sp_connection_settings = sp_list_sorted[i]['connectionSettings']
            sp_uri = sp_list_sorted[i]['uri']
            etag = sp_list_sorted[i]['eTag']
            sp_name = sp_list_sorted[i]['name']
            conn_set = sp_connection_settings['connections']
            countdown(0, 15)
            for x in range(0, len(conn_set)):
                if x == 0:
                    wwnn1 = conn_set[x]['wwnn']
                    wwpn1 = conn_set[x]['wwpn']
                elif x == 1:
                    wwnn2 = conn_set[x]['wwnn']
                    wwpn2 = conn_set[x]['wwpn']
            if sp_name == "Server Profile 1":
                update_sp_inst.UpdateServerProfileLuns(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                       sp_descr[i], requested_bw, fc_net_enc1_bay1_uri,
                                                       fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                       wwpn2, mode, etag)
            elif sp_name == "Server Profile 4":
                update_sp_inst.UpdateServerProfileBootFromSAN(ip, auth, api, sp_name, sp_uri, server_hw_uri,
                                                              enc_grp_uri, sp_descr[i], requested_bw,
                                                              fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, id_1[i],
                                                              id_2[i], wwnn1, wwpn1, array_wwpn1, wwnn2, wwpn2,
                                                              array_wwpn2, mode, etag)
            elif sp_name == "Server Profile 2":
                update_sp_inst.UpdateServerProfileLuns(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                       sp_descr[i], requested_bw, fc_net_enc1_bay1_uri,
                                                       fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                       wwpn2, mode, etag)
            elif sp_name == "Server Profile 3":
                update_sp_inst.UpdateServerProfileLuns(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                       sp_descr[i], requested_bw, fc_net_enc1_bay1_uri,
                                                       fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                       wwpn2, mode, etag)
            else:
                pass

        logging.info("Pausing 7mins for server profiles to be updated before powering on the servers")
        countdown(7, 0)
        logging.info("*******************POWERING ON SERVERS **********************************")

        tc = "Update Server Profiles"
        logging.info("Checking status of server profiles")
        sp_status = GetSPStatus(ip, auth, api)
        if sp_status == "Normal":
            result = "Pass"
        else:
            result = "Fail"

        PassOrFail(result, tc)
        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(8, 0)
        logging.info("Checking FC Connections are set to 32GB speed in Server Profiles")
        sp_speeds.ServerProfileConnectionSpeed32GB(ip, auth, api)
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_carbon.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        logging.info("*******************POWERING OFF SERVERS *************************************")
        power_cycle_server_inst.power_off_servers(ip, auth, api)

        logging.info("Getting Enclosure Group")
        enc_inst = Enclosures()
        enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
        enc_grp_name_uri = printDict(enc_grp_dict, ['name', 'uri'])
        enc_grp_uri = enc_grp_name_uri[0]['uri']

        logging.info("Getting Server HW and Profiles")
        server_hw_profiles = Servers()
        array_wwpn1, array_wwpn2, wwnn1_start, wwpn1_start, wwnn2_start, wwpn2_start = server_hw_profiles.server_wwnn_start_wwpn_start(
            eagle)
        sp_name, sp_descr, id_1, id_2 = server_hw_profiles.server_profile_config()
        wwnn1, wwpn1, wwnn2, wwpn2 = server_hw_profiles.server_wwwn_wwpn(wwnn1_start, wwpn1_start, wwnn2_start,
                                                                         wwpn2_start)
        sp_dict = server_hw_profiles.ServerProfiles(ip, auth, api)
        sp_list = printDict(sp_dict,
                            ['name', 'uri', 'state', 'serverHardwareUri', 'enclosureBay', 'eTag', 'connectionSettings'])
        sp_list_sorted = sorted(sp_list)

        logging.info("*******************UPDATING FC CONNECTIONS TO 16GB***************************")
        requested_bw = "16000"
        mode = "UEFI"

        logging.info("Starting Server Profile list loop")
        for i, value in enumerate(sp_list_sorted):
            server_hw_uri = sp_list_sorted[i]['serverHardwareUri']
            sp_connection_settings = sp_list_sorted[i]['connectionSettings']
            sp_uri = sp_list_sorted[i]['uri']
            etag = sp_list_sorted[i]['eTag']
            sp_name = sp_list_sorted[i]['name']
            conn_set = sp_connection_settings['connections']
            countdown(0, 15)
            for x in range(0, len(conn_set)):
                if x == 0:
                    wwnn1 = conn_set[x]['wwnn']
                    wwpn1 = conn_set[x]['wwpn']
                elif x == 1:
                    wwnn2 = conn_set[x]['wwnn']
                    wwpn2 = conn_set[x]['wwpn']
            if sp_name == "Server Profile 1":
                update_sp_inst.UpdateServerProfileLuns(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                       sp_descr[i], requested_bw, fc_net_enc1_bay1_uri,
                                                       fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                       wwpn2, mode, etag)
            elif sp_name == "Server Profile 4":
                update_sp_inst.UpdateServerProfileBootFromSAN(ip, auth, api, sp_name, sp_uri, server_hw_uri,
                                                              enc_grp_uri, sp_descr[i], requested_bw,
                                                              fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, id_1[i],
                                                              id_2[i], wwnn1, wwpn1, array_wwpn1, wwnn2, wwpn2,
                                                              array_wwpn2, mode, etag)
            elif sp_name == "Server Profile 2":
                update_sp_inst.UpdateServerProfileLuns(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                       sp_descr[i], requested_bw, fc_net_enc1_bay1_uri,
                                                       fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                       wwpn2, mode, etag)
            elif sp_name == "Server Profile 3":
                update_sp_inst.UpdateServerProfileLuns(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                       sp_descr[i], requested_bw, fc_net_enc1_bay1_uri,
                                                       fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                       wwpn2, mode, etag)
            else:
                pass

        logging.info("Pausing 6mins for server profiles to be updated before powering on the servers")
        countdown(7, 0)
        logging.info("*******************POWERING ON SERVERS **********************************")

        tc = "Update Server Profiles"
        logging.info("Checking status of server profiles")
        sp_status = GetSPStatus(ip, auth, api)
        if sp_status == "Normal":
            result = "Pass"
        else:
            result = "Fail"

        PassOrFail(result, tc)

        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(8, 0)
        logging.info("Checking FC Connections are set to 16Gb speed in Server Profiles")
        sp_speeds.ServerProfileConnectionSpeed16GB(ip, auth, api)
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_carbon.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        logging.info("*******************POWERING OFF SERVERS *************************************")
        power_cycle_server_inst.power_off_servers(ip, auth, api)

        logging.info("Getting Enclosure Group")
        enc_inst = Enclosures()
        enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
        enc_grp_name_uri = printDict(enc_grp_dict, ['name', 'uri'])
        enc_grp_uri = enc_grp_name_uri[0]['uri']

        logging.info("Getting Server HW and Profiles")
        server_hw_profiles = Servers()
        array_wwpn1, array_wwpn2, wwnn1_start, wwpn1_start, wwnn2_start, wwpn2_start = server_hw_profiles.server_wwnn_start_wwpn_start(
            eagle)
        sp_name, sp_descr, id_1, id_2 = server_hw_profiles.server_profile_config()
        wwnn1, wwpn1, wwnn2, wwpn2 = server_hw_profiles.server_wwwn_wwpn(wwnn1_start, wwpn1_start, wwnn2_start,
                                                                         wwpn2_start)
        sp_dict = server_hw_profiles.ServerProfiles(ip, auth, api)
        sp_list = printDict(sp_dict,
                            ['name', 'uri', 'state', 'serverHardwareUri', 'enclosureBay', 'eTag', 'connectionSettings'])
        sp_list_sorted = sorted(sp_list)

        logging.info("*******************UPDATING FC CONNECTIONS TO Auto***************************")
        requested_bw = "Auto"
        mode = "UEFI"

        logging.info("Starting Server Profile list loop")
        for i, value in enumerate(sp_list_sorted):
            server_hw_uri = sp_list_sorted[i]['serverHardwareUri']
            sp_connection_settings = sp_list_sorted[i]['connectionSettings']
            sp_uri = sp_list_sorted[i]['uri']
            etag = sp_list_sorted[i]['eTag']
            sp_name = sp_list_sorted[i]['name']
            conn_set = sp_connection_settings['connections']
            countdown(0, 15)
            for x in range(0, len(conn_set)):
                if x == 0:
                    wwnn1 = conn_set[x]['wwnn']
                    wwpn1 = conn_set[x]['wwpn']
                elif x == 1:
                    wwnn2 = conn_set[x]['wwnn']
                    wwpn2 = conn_set[x]['wwpn']
            if sp_name == "Server Profile 1":
                update_sp_inst.UpdateServerProfileLuns(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                       sp_descr[i], requested_bw, fc_net_enc1_bay1_uri,
                                                       fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                       wwpn2, mode, etag)
            elif sp_name == "Server Profile 4":
                update_sp_inst.UpdateServerProfileBootFromSAN(ip, auth, api, sp_name, sp_uri, server_hw_uri,
                                                              enc_grp_uri, sp_descr[i], requested_bw,
                                                              fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, id_1[i],
                                                              id_2[i], wwnn1, wwpn1, array_wwpn1, wwnn2, wwpn2,
                                                              array_wwpn2, mode, etag)
            elif sp_name == "Server Profile 2":
                update_sp_inst.UpdateServerProfileLuns(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                       sp_descr[i], requested_bw, fc_net_enc1_bay1_uri,
                                                       fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                       wwpn2, mode, etag)
            elif sp_name == "Server Profile 3":
                update_sp_inst.UpdateServerProfileLuns(ip, auth, api, sp_name, sp_uri, server_hw_uri, enc_grp_uri,
                                                       sp_descr[i], requested_bw, fc_net_enc1_bay1_uri,
                                                       fc_net_enc1_bay4_uri, id_1[i], id_2[i], wwnn1, wwpn1, wwnn2,
                                                       wwpn2, mode, etag)
            else:
                pass

        logging.info("Pausing 6mins for server profiles to be updated before powering on the servers")
        countdown(7, 0)
        logging.info("*******************POWERING ON SERVERS **********************************")

        tc = "Update Server Profiles"
        logging.info("Checking status of server profiles")
        sp_status = GetSPStatus(ip, auth, api)
        if sp_status == "Normal":
            result = "Pass"
        else:
            result = "Fail"

        PassOrFail(result, tc)

        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(8, 0)
        logging.info("Checking FC Connections are set to Auto speed in Server Profiles")
        sp_speeds.ServerProfileConnectionSpeedAuto32GB(ip, auth, api)
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_carbon.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        counter += 1
        countdown(1, 0)
        logging.info("Starting next iteration")


def testcase_aside_bside_ligs(auth, tor_ip, enc_name):
    logging.testcases("########################################")
    logging.testcases("TestCase: UFG LE with A-Side B-side LIGs")
    logging.testcases("########################################")

    testcase = 'UFG LE with A-Side B-side LIGs'
    counter = 0
    tor_pw = 'hpvse123'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    countdown(0, 5)

    # instantiation of Classes
    all_states_inst = CheckAllStatesOfCarbon()
    create_lig_inst = CreateLogicalInterconnectGroup()
    power_cycle_server_inst = PowerOffOnServers()
    retrieve_net_inst = Networks()
    enc_inst = Enclosures()
    get_num_flogi_inst = GetFLOGI()

    logging.info("*******************CREATING A-SIDE AND B-SIDE LIGs ***************************")

    logging.info("Getting interconnect types uri")
    ic_types_inst = Interconnects()
    ic_types_list = ic_types_inst.GetInterconnectTypes(ip, auth, api)
    ic_types_name_uri = printDict(ic_types_list, ['uri', 'name'])

    logging.info("Getting Fc network URIs")
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle21(
        ip, auth, api)

    logging.info("Getting list of LIGs")
    ligs_inst = LogicalInterconnectGroup()
    ligs_list = ligs_inst.GetListOfLIGs(ip, auth, api)
    ligs_name_uri = printDict(ligs_list, ['name', 'uri'])

    for i, value in enumerate(ligs_name_uri):
        lig_name = ligs_name_uri[i]['name']
        if lig_name == 'LIG_A-SIDE':
            logging.info("These LIGs exist, skiping LIG creation")
            break
        elif lig_name == 'LIG_B-SIDE':
            logging.info("These LIGs exist, skiping LIG creation")
            break
        else:
            print "Those ligs do not exist, creating new LIGs"
            # Create two LIGs(A-side and B-side) with 1 uplink set per LIG in TBird enc.
            logging.info("Creating a LIGs")
            for s in range(0, len(ic_types_name_uri)):
                ic_uri = ic_types_name_uri[s]['uri']
                ic_name = ic_types_name_uri[s]['name']
                if ic_name == "Virtual Connect SE 32Gb FC Module for Synergy":
                    create_lig_inst.CreateLigASideE155Trunk(ip, auth, api, ic_uri, fc_mode, v3_enabled,
                                                            fc_net_enc1_bay1_uri, fc_net_enc1_bay1_quri,
                                                            consistency_check)
                    create_lig_inst.CreateLigBSideE155Trunk(ip, auth, api, ic_uri, fc_mode, fc_net_enc1_bay4_uri,
                                                            v3_enabled, consistency_check)
            logging.info("Pausing 20 secs for the LIGs to be created")
            countdown(0, 20)

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
            if lig_name == "LIG_A-SIDE":
                lig1_uri = ligs_name_uri[i]['uri']
            elif lig_name == "LIG_B-SIDE":
                lig2_uri = ligs_name_uri[i]['uri']

        update_enc_grp_inst = UpdateEG()
        update_enc_grp_inst.UpdateEgE21(ip, auth, api, enc_grp_uri, enc_grp_etag, lig1_uri, lig2_uri)

        logging.info("Pausing for 30 secs for EG to be updated")
        countdown(0, 30)

        logging.info("*******************UPDATING LE ***************************")
        logging.info("Getting Logical Enclosure")
        le_inst = LogicalEnclosure()
        le_list = le_inst.GetLogicalEnclosure(ip, auth, api)
        le_uri_list = printDict(le_list, ['uri'])
        le_uri = le_uri_list[0]['uri']

        logging.info("Updating LE from group")
        update_le = UpdateLogicalEnclosure()
        update_le.LeUpdateFromGroup(ip, auth, api, le_uri)

        logging.info("Pausing for 10mins to wait for the LE to updated from group")
        countdown(10, 0)
        power_cycle_server_inst.power_off_servers(ip, auth, api)
        countdown(1, 0)

        logging.info("Checking status of LE")
        GetStatusOfLogicalEnclosure(ip, auth, api)

        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(7, 0)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

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

        for i, value in enumerate(ligs_name_uri):
            lig_name = ligs_name_uri[i]['name']
            if lig_name == "LIG":
                lig1_uri = ligs_name_uri[i]['uri']
        update_enc_grp_inst.UpdateEgDefaultE21(ip, auth, api, enc_grp_uri, enc_grp_etag, lig1_uri)

        logging.info("Pausing for 30 secs for EG to be created")
        countdown(0, 30)

        logging.info("Updating LE from group")
        update_le.LeUpdateFromGroup(ip, auth, api, le_uri)

        logging.info("********************UPDATE FROM GROUP THE LE***************************")

        logging.info("Pausing for 10mins for LE to be updated from group")
        countdown(10, 0)
        power_cycle_server_inst.power_off_servers(ip, auth, api)
        countdown(1, 0)

        logging.info("Checking status of LE")
        GetStatusOfLogicalEnclosure(ip, auth, api)

        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(7, 0)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        counter += 1
        countdown(1, 0)


def testcase_port_mirror(auth, tor_ip, enc_name):
    logging.testcases("########################################################################")
    logging.testcases("TestCase: Configure Port Monitor, Bi-directional, To Server, From Server")
    logging.testcases("########################################################################")

    testcase = 'Configure Port Monitor, Bi-directional, To Server, From Server'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()
    logging.info("Getting Interconnects")
    ic_dict = Interconnects()
    get_ic_list = ic_dict.GetInterconnect(ip, auth, api)
    ic_name_uri_list = printDict(get_ic_list, ['productName', 'name', 'ports', 'enclosureName'])

    logging.info("Getting list of DL and UL ports to use for port monitor")
    for i, value in enumerate(ic_name_uri_list):
        ports_list = ic_name_uri_list[i]['ports']
        ic_name = ic_name_uri_list[i]['name']
        name = ic_name_uri_list[i]['enclosureName']
        if ic_name == "{}, interconnect 1".format(name):
            for p in range(0, len(ports_list)):
                port_name = ports_list[p]['portName']
                port_uri = ports_list[p]['uri']
                if port_name == "5":
                    ul_port_uri = port_uri
                if port_name == "d1":
                    dl_port_uri = port_uri

    # logging.info("Getting list of logical interconnects")
    logging.info("Getting Logical Interconnects")
    li_inst = LogicalInterconnects()
    li_list = li_inst.GetLogicalInterconnects(ip, auth, api)
    li_list_uri_name = printDict(li_list, ['uri', 'name'])

    for i, value in enumerate(li_list_uri_name):
        li_name = li_list_uri_name[i]['name']
        li_uri_list = li_list_uri_name[i]['uri']
        if li_name == "LE-LIG1-1":
            li_uri = li_uri_list
        elif li_name == "LE-LIG-1":
            li_uri = li_uri_list
        elif li_name == "LE-LIG":
            li_uri = li_uri_list

    logging.info("Setting Port Monitor to 'Bi-Directional'")
    config_port_monitor_inst = PortMonitor()
    config_port_monitor_inst.ConfigPortMonitorBiDir(ip, api, auth, li_uri, ul_port_uri, dl_port_uri)
    countdown(5, 0)
    tc = "Port Monitor is set to Bi-Directional"
    pm_config_info = config_port_monitor_inst.CheckPortMonitorConfigInfo(ip, api, auth, li_uri)
    if pm_config_info == "MonitoredBoth":
        result = "Pass"
        PassOrFail(result, tc)
    else:
        result = "Fail"
        PassOrFail(result, tc)
        sys.exit(0)

    logging.info("Checking Link Status of Monitored Port")
    mp_port_status = config_port_monitor_inst.CheckMpStatusLinked(ip, api, auth, li_uri)
    print mp_port_status
    tc = "Monitored Port Status"
    if mp_port_status == "Linked":
        result = "Pass"
        PassOrFail(result, tc)
    elif mp_port_status == "Unlinked":
        result = "Fail"
        PassOrFail(result, tc)

    logging.info("Checking Link Status of Analyzer Port")
    ap_port_status = config_port_monitor_inst.CheckApStatusLinked(ip, api, auth, li_uri)
    print ap_port_status
    tc = "Analyzer Port Status"
    if ap_port_status == "Linked":
        result = "Pass"
        PassOrFail(result, tc)
    elif ap_port_status == "Unlinked":
        result = "Fail"
        PassOrFail(result, tc)

    logging.info("Setting Port Monitor to 'From Server'")
    config_port_monitor_inst.ConfigPortMonitorFromServer(ip, api, auth, li_uri, ul_port_uri, dl_port_uri)
    countdown(5, 0)
    logging.info("Checking Port Monitor is set to 'From Server'")
    tc = "Port Monitor is set to From Server"
    pm_config_info = config_port_monitor_inst.CheckPortMonitorConfigInfo(ip, api, auth, li_uri)
    if pm_config_info == "MonitoredFromServer":
        result = "Pass"
        PassOrFail(result, tc)
    else:
        result = "Fail"
        PassOrFail(result, tc)
        sys.exit(0)

    logging.info("Checking Link Status of Monitored Port")
    mp_port_status = config_port_monitor_inst.CheckMpStatusLinked(ip, api, auth, li_uri)
    print mp_port_status
    tc = "Monitored Port Status"
    if mp_port_status == "Linked":
        result = "Pass"
        PassOrFail(result, tc)
    elif mp_port_status == "Unlinked":
        result = "Fail"
        PassOrFail(result, tc)

    logging.info("Checking Link Status of Analyzer Port")
    ap_port_status = config_port_monitor_inst.CheckApStatusLinked(ip, api, auth, li_uri)
    print ap_port_status
    tc = "Analyzer Port Status"
    if ap_port_status == "Linked":
        result = "Pass"
        PassOrFail(result, tc)
    elif ap_port_status == "Unlinked":
        result = "Fail"
        PassOrFail(result, tc)

    logging.info("Setting Port Monitor to To Server")
    config_port_monitor_inst.ConfigPortMonitorToServer(ip, api, auth, li_uri, ul_port_uri, dl_port_uri)
    countdown(5, 0)
    logging.info("Checking Port Monitor is set to 'To Server'")
    tc = "Port Monitor is set to To Server"
    pm_config_info = config_port_monitor_inst.CheckPortMonitorConfigInfo(ip, api, auth, li_uri)
    if pm_config_info == "MonitoredToServer":
        result = "Pass"
        PassOrFail(result, tc)
    else:
        result = "Fail"
        PassOrFail(result, tc)
        sys.exit(0)

    logging.info("Checking Link Status of Monitored Port")
    mp_port_status = config_port_monitor_inst.CheckMpStatusLinked(ip, api, auth, li_uri)
    print mp_port_status
    tc = "Monitored Port Status"
    if mp_port_status == "Linked":
        result = "Pass"
        PassOrFail(result, tc)
    elif mp_port_status == "Unlinked":
        result = "Fail"
        PassOrFail(result, tc)

    logging.info("Checking Link Status of Analyzer Port")
    ap_port_status = config_port_monitor_inst.CheckApStatusLinked(ip, api, auth, li_uri)
    print ap_port_status
    tc = "Analyzer Port Status"
    if ap_port_status == "Linked":
        result = "Pass"
        PassOrFail(result, tc)
    elif ap_port_status == "Unlinked":
        result = "Fail"
        PassOrFail(result, tc)

    config_port_monitor_inst.DisablePortMonitor(ip, api, auth, li_uri, ul_port_uri, dl_port_uri)
    countdown(5, 0)
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


def testcase_portspeed_8_16_32_tor(auth, tor_ip, enc_name):
    logging.testcases("#######################################################")
    logging.testcases("TestCase: Change port speeds(8/16/32GB) on ToR FC switch")
    logging.testcases("#######################################################")

    tor_un = 'admin'
    tor_pw = 'hpvse123'

    testcase = 'Change port speeds(8/16/32GB) on ToR FC switch'
    logging.info("Checking the status of the downlink and uplink ports before starting the test")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    port_speed = ConfigureTOR()
    carbon_port_speed = GetCarbonPortStatus()
    get_num_flogi_inst = GetFLOGI()
    all_states_inst = CheckAllStatesOfCarbon()
    countdown(0, 10)

    logging.testcases("Port speed set to 8Gb")
    port_speed.ConfigPortSpeed8GbE21TORPort16_19(tor_ip, tor_un, tor_pw)
    port_speed.ConfigPortSpeed8GbE21TORPort8_11(tor_ip, tor_un, tor_pw)
    countdown(3, 0)

    logging.info("Checking to see if ports are set to 8Gb")
    carbon_port_speed.GetCarbonUpLinkPortSpeed8Gb(ip, api, auth)
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

    logging.testcases("Port speed set to 16Gb")
    port_speed.ConfigPortSpeed16GbE21TORPort16_19(tor_ip, tor_un, tor_pw)
    port_speed.ConfigPortSpeed16GbE21TORPort8_11(tor_ip, tor_un, tor_pw)
    countdown(3, 0)

    logging.info("Checking to see if ports are set to 16Gb")
    carbon_port_speed.GetCarbonUpLinkPortSpeed16Gb(ip, api, auth)
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

    logging.testcases("Port speed set to 32Gb")
    port_speed.ConfigPortSpeed32GbE155TORPort16_19(tor_ip, tor_un, tor_pw)
    port_speed.ConfigPortSpeed32GbE155TORPort8_11(tor_ip, tor_un, tor_pw)
    countdown(3, 0)

    logging.info("Checking to see if ports are set to 32Gb")
    carbon_port_speed.GetCarbonUpLinkPortSpeed32Gb(ip, api, auth)
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

    logging.testcases("Port speed set to Auto")
    port_speed.ConfigPortSpeedAutobE21TORPort16_19(tor_ip, tor_un, tor_pw)
    port_speed.ConfigPortSpeedAutobE21TORPort8_11(tor_ip, tor_un, tor_pw)
    countdown(3, 0)

    logging.info("Checking to see if ports are set to Auto 32Gb")
    carbon_port_speed.GetCarbonUpLinkPortSpeed32Gb(ip, api, auth)
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


def testcase_remove_add_fc_network_li(auth, tor_ip, enc_name):
    logging.testcases("################################################")
    logging.testcases("TestCase: Remove/Add FC Network from ULS from LI")
    logging.testcases("################################################")

    testcase = 'Remove/Add FC Network from ULS from LI'
    counter = 0
    # Check UL and DL port status on both carbons before starting test
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    all_states_inst = CheckAllStatesOfCarbon()
    uplink_link_sets_inst = AddRemoveUplinkSetsLi()
    get_num_flogi_inst = GetFLOGI()
    retrieve_net_inst = Networks()
    countdown(0, 5)

    logging.info("Getting Enclosures ")
    enc_inst = Enclosures()
    enc_dict = enc_inst.GetEnc(ip, auth, api)
    enc_name_uri_list = printDict(enc_dict, ['enclosureModel', 'name', 'uri'])
    enc_uri = enc_name_uri_list[0]['uri']

    logging.info("Getting Fc network URIs")
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle21(
        ip, auth, api)

    logging.info("Getting Logical Interconnects")
    get_li_instance = LogicalInterconnects()
    li_list = get_li_instance.GetLogicalInterconnects(ip, auth, api)
    li_name_uri = printDict(li_list, ['uri', 'name'])
    for n, value in enumerate(li_name_uri):
        LiName = li_name_uri[n]['name']
        LIuri = li_name_uri[n]['uri']
        if LiName == "LE-LIG-1":
            li_uri = LIuri
        elif LiName == "LE-LIG-ETH":
            li_uri = LIuri

    logging.info("Getting Uplink Sets")
    get_li_instance = LogicalInterconnects()
    uplink_set_list = get_li_instance.GetUplinkSets(ip, auth, api)
    uplink_set_uri_name = printDict(uplink_set_list, ['uri', 'name'])
    for n, value in enumerate(uplink_set_uri_name):
        uls_name = uplink_set_uri_name[n]['name']
        uls_uri = uplink_set_uri_name[n]['uri']
        if uls_name == "BAY1":
            uls_bay1_uri = uls_uri
        elif uls_name == "BAY4":
            uls_bay4_uri = uls_uri

    countdown(0, 10)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Removing FC network from Bay1 Uplink Set")
        uplink_link_sets_inst.RemoveUlsBay1FcNetworkLi(ip, auth, api, li_uri, enc_uri, uls_bay1_uri)
        countdown(5, 0)

        logging.info("Adding FC network to Bay1 Uplink Set")
        uplink_link_sets_inst.AddUlsBay1FcNetworkLi(ip, auth, api, fc_net_enc1_bay1_uri, li_uri, enc_uri, uls_bay1_uri)
        countdown(7, 0)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        logging.info("Removing FC network from Bay4 Uplink Set")
        uplink_link_sets_inst.RemoveUlsBay4FcNetworkLi(ip, auth, api, li_uri, enc_uri, uls_bay4_uri)
        countdown(5, 0)

        logging.info("Adding FC network to Bay4 Uplink Set")
        uplink_link_sets_inst.AddUlsBay4FcNetworkLi(ip, auth, api, fc_net_enc1_bay4_uri, li_uri, enc_uri, uls_bay4_uri)
        countdown(7, 0)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        counter += 1
        countdown(0, 30)


def testcase_remove_add_lig_encgrp(auth, tor_ip, enc_name):
    logging.testcases("################################################")
    logging.testcases("TestCase: Remove/Add LIG from/to Enclosure Group")
    logging.testcases("################################################")

    testcase = 'Remove/Add LIG from/to Enclosure Group'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()
    countdown(0, 5)

    logging.info("Getting list of LIGs")
    ligs = LogicalInterconnectGroup()
    lig_list = ligs.GetListOfLIGs(ip, auth, api)
    lig_name_uri = printDict(lig_list, ['name', 'uri'])

    logging.info("Getting Enclosure Group ")
    enc_inst = Enclosures()
    enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
    enc_grp_list = printDict(enc_grp_dict, ['name', 'uri', 'eTag'])
    enc_grp_uri = enc_grp_list[0]['uri']
    enc_grp_etag = enc_grp_list[0]['eTag']

    for i, value in enumerate(lig_name_uri):
        lig_name = lig_name_uri[i]['name']
        if lig_name == "LIG_A-SIDE":
            lig1_uri = lig_name_uri[i]['uri']
        elif lig_name == "LIG_B-SIDE":
            pass

    logging.info("Powering off servers before removing LIGs")
    power_cycle_server_inst = PowerOffOnServers()
    power_cycle_server_inst.power_off_servers(ip, auth, api)
    countdown(1, 0)

    update_enc_grp_inst = UpdateEG()
    # Function to update EG with no LIGs
    logging.info("**********Removing LIGs from Enclosure Group**************")
    update_enc_grp_inst.UpdateEgNoLIGsE21(ip, auth, api, enc_grp_uri, enc_grp_etag)
    countdown(0, 20)

    logging.info("*******************UPDATING LE ***************************")

    logging.info("Getting Logical Enclosure")
    le_inst = LogicalEnclosure()
    le_list = le_inst.GetLogicalEnclosure(ip, auth, api)
    le_uri_list = printDict(le_list, ['uri'])
    le_uri = le_uri_list[0]['uri']

    logging.info("Updating LE from group")
    update_le = UpdateLogicalEnclosure()
    update_le.LeUpdateFromGroup(ip, auth, api, le_uri)

    logging.info("Pausing for 2mins to wait for the LE to updated from group")
    countdown(2, 0)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    logging.info("*******************RESETTING EG TO DEFAULT VALUES ***************************")

    logging.info("Getting list of LIGs")
    ligs = LogicalInterconnectGroup()
    lig_list = ligs.GetListOfLIGs(ip, auth, api)
    lig_name_uri = printDict(lig_list, ['name', 'uri'])

    logging.info("Getting Enclosure Group ")
    enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
    enc_grp_list = printDict(enc_grp_dict, ['name', 'uri', 'eTag'])
    enc_grp_uri = enc_grp_list[0]['uri']
    enc_grp_etag = enc_grp_list[0]['eTag']

    for i, value in enumerate(lig_name_uri):
        lig_name = lig_name_uri[i]['name']
        if lig_name == "LIG":
            lig1_uri = lig_name_uri[i]['uri']
    update_enc_grp_inst.UpdateEgDefaultE21(ip, auth, api, enc_grp_uri, enc_grp_etag, lig1_uri)

    logging.info("Pausing for 20 secs for EG to be updated")
    countdown(0, 20)

    logging.info("Updating LE from group")
    update_le.LeUpdateFromGroup(ip, auth, api, le_uri)

    logging.info("********************UPDATE FROM GROUP THE LE***************************")

    logging.info("Pausing for 10mins for LE to be updated from group")
    countdown(5, 0)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    logging.info("Pausing 5 mins to power on servers and boot into OS")
    power_cycle_server_inst.power_on_servers(ip, auth, api)
    countdown(5, 0)

    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)


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

    counter = 0
    logging.info("Checking the status of the downlink and uplink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    all_states_inst = CheckAllStatesOfCarbon()
    carbon_reset_inst = PowerStateOfCarbon()
    get_num_flogi_inst = GetFLOGI()

    logging.info("Getting Interconnects")
    ic_dict = Interconnects()
    get_ic_dict = ic_dict.GetInterconnect(ip, auth, api)
    ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])

    countdown(0, 5)

    # While loop to reset carbon ICMs
    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        testcase = "Carbon Reset test bay4"
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

        countdown(7, 0)
        logging.info("Checking to see the state of the carbon in bay4")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)

        # For loop to iterate thru carbon bay1 and power it off
        logging.info("Resetting the carbon ICMs in bay1")
        testcase = "Carbon Reset test bay1"
        for ic, value in enumerate(ic_name_uri_list):
            icm_uri = ic_name_uri_list[ic]['uri']
            icm_name = ic_name_uri_list[ic]['name']
            name = ic_name_uri_list[ic]['enclosureName']
            if icm_name == "{}, interconnect 1".format(name):
                logging.info("Performing Reset operation on the carbon in {}".format(icm_name))
                carbon_reset_inst.ResetCarbon(ip, auth, api, icm_uri)
            else:
                pass

        countdown(7, 0)
        logging.info("Checking to see the state of the carbon in bay4")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        counter += 1
        countdown(0, 30)
        logging.info("Starting next iteration")


def testcase_carbon_hostname(auth):
    logging.testcases("########################################")
    logging.testcases("TestCase: Update/Reset carbon32 hostname")
    logging.testcases("########################################")
    logging.info("Getting Interconnects info")
    api = '2200'
    ic_inst = Interconnects()
    get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
    ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])
    logging.info("Resetting hostname on carbon in bay1 to default before running test")
    carbon_location = 'MXQ81306V8, interconnect 1'
    reset_hostname = ''
    for ic, value in enumerate(ic_name_uri_list):
        ic_uri = ic_name_uri_list[ic]['uri']
        ic_name = ic_name_uri_list[ic]['name']
        name = ic_name_uri_list[ic]['enclosureName']
        if ic_name == carbon_location:
            ic_inst.CarbonHostnameUpdate(ip, auth, api, ic_uri, reset_hostname)
            logging.info("pausing 20 secs before fetching carbon hostname")
            countdown(0, 20)
            pretest_carbon_hn = ic_inst.getCarbonHostname(ip, auth, api, name, carbon_location)
            logging.info(pretest_carbon_hn)
        else:
            pass

    new_hostname = 'eagle155-bay1'
    ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])
    logging.info("Updating hostname on carbon in bay1")
    for ic, value in enumerate(sorted(ic_name_uri_list)):
        ic_uri = ic_name_uri_list[ic]['uri']
        ic_name = ic_name_uri_list[ic]['name']
        name = ic_name_uri_list[ic]['enclosureName']
        if ic_name == carbon_location:
            ic_inst.CarbonHostnameUpdate(ip, auth, api, ic_uri, new_hostname)
            logging.info("pausing 20 secs before fetching carbon hostname")
            countdown(0, 20)
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
            countdown(0, 20)
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
    api = '2200'
    ic_inst = Interconnects()
    for name in enc_name:
        GetInterconnectList = ic_inst.GetInterconnectMultiEnc(ip, auth, api, name)
        ic_list = printDict(GetInterconnectList, ['model', 'ports', 'firmwareVersion'])
        logging.info("Getting a list of uplink ports that are online\n")
        for i in range(0, len(ic_list)):
            PortList = ic_list[i]['ports']
            model = ic_list[i]['model']
            fw_ver = ic_list[i]['firmwareVersion']
            if model == "Virtual Connect SE 32Gb FC Module for Synergy":
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
    countdown(0, 5)

    backup_restore_inst.create_appl_backup(ip, auth, api, eagle)
    logging.info("Creating appliance backup")
    countdown(2, 0)
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
    countdown(45, 0)
    restore_status_dict = backup_restore_inst.GetApplianceRestoreStatus(ip, api)
    restore_status_list = printDict(restore_status_dict, ['status', 'progressStep', 'completedPhaseSteps', 'totalPhaseSteps', 'restorePhase'])
    for i, value in enumerate(restore_status_list):
        status = restore_status_list[i]['status']
        progress_step = restore_status_list[i]['progressStep']
        completed_step = restore_status_list[i]['completedPhaseSteps']
        total_steps = restore_status_list[i]['totalPhaseSteps']
        restore_phase = restore_status_list[i]['restorePhase']
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
                countdown(5, 0)

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
    countdown(0, 5)

    logging.info("Creating LE Supportdump")
    le_inst = LogicalEnclosure()
    support_dump, file_name = le_inst.Create_le_support_dump(ip, auth, api, encrypted, eagle)
    logging.info("support dump path {}" .format(support_dump))
    logging.info("decrypting support dump file")
    subprocess.Popen('decrypt-support-dump.bat {} ' .format(support_dump))
    countdown(0, 20)
    logging.info("Filename being passed to untar_supportdump function: {}" .format(file_name))
    untar_supportdump(file_name, eagle)
    
    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)




def testcase_redistribute_login(auth, tor_ip, enc_name):
    logging.testcases("################################################")
    logging.testcases("TestCase: Redistribution Logins; Auto and Manual")
    logging.testcases("################################################")

    testcase = 'Redistribute Logins Auto/Manual'
    counter = 0
    tor_pw = 'hpvse123'
    icm_name_rdl = 'MXQ81306V8, interconnect 1'
    port_list = ['8','9','10']
    fc_net_name = 'BAY1'
    #Check UL and DL port status on both carbons before starting test
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth, enc_name)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth, enc_name)
    all_states_inst = CheckAllStatesOfCarbon()
    ic_inst = Interconnects()
    cfg_trunk_inst = ConfigureTOR()
    li_inst = LogicalInterconnects()
    update_net_inst = UpdateNetworks()
    get_num_flogi_inst = GetFLOGI()
    retrieve_net_inst = Networks()
    countdown(0, 5)

    logging.info("Getting Uplink set URIs")
    uls_enc1_bay1_uri, uls_enc1_bay4_uri = retrieve_net_inst.get_uplink_set_uri_eagle155(ip, auth, api)

    logging.info("Getting Logical Interconnects")
    get_li_instance = LogicalInterconnects()
    li_list = get_li_instance.GetLogicalInterconnects(ip, auth, api)
    li_name_uri = printDict(li_list, ['uri', 'name'])
    for n, value in enumerate(li_name_uri):
        LiName = li_name_uri[n]['name']
        LIuri = li_name_uri[n]['uri']
        if LiName == "LE-LIG-1":
            li_uri = LIuri
        else:
            pass

    tc = "Validate of Number of logins"
    logging.info("Checking status of current logins prior to test")
    ic_ports_uri_count = ic_inst.get_fc_logins_before(ip, auth, api, enc_name, icm_name_rdl)
    uri_count = (len(ic_ports_uri_count))
    if uri_count == 1:
        result = "Pass"
        logging.info("port count with logins: {}".format(len(ic_ports_uri_count)))
    else:
        result = "Fail"
        logging.warning("port count with logins: {}".format(len(ic_ports_uri_count)))
    PassOrFail(result, tc)

    logging.info("Disabling trunking on ToR ports")
    cfg_trunk_inst.DisableTrunkingOnE21TORPort8_11(tor_ip, tor_un, tor_pw)
    countdown(3, 0)


    auto_login_dist_false = 'false'
    link_stab_time = '30'
    logging.info("Setting FC network RDL to Manual.")
    update_net_inst.update_network_rdl_func(ip, auth, api, fc_net_name, link_stab_time, auto_login_dist_false)

    countdown(1, 0)
    logging.info("Disabling ports on the ToR")
    cfg_trunk_inst.PersistenDisablePortsTor(tor_ip, tor_un, tor_pw, port_list)

    countdown(2, 30)
    logging.info("Enabling ports on the ToR")
    cfg_trunk_inst.PersistenEnablePortsTor(tor_ip, tor_un, tor_pw, port_list)

    countdown(2, 30)
    logging.info("Redistributing logins")
    headers_dict =li_inst.RedistributeLogins(ip, api, auth, li_uri, uls_enc1_bay1_uri)
    task_uri = headers_dict['Location']
    logging.info("The Redistributing logins task is: {}" .format(task_uri))
    countdown(0, 5)
    task_dict = get_task(ip, auth, api, task_uri)
    task_state = task_dict['taskState']
    while task_state == 'Running':
        task_dict = get_task(ip, auth, api, task_uri)
        task_state = task_dict['taskState']
        logging.info("The state of Redistributing logins task: {}" .format(task_state))
        if task_state == 'Running':
            logging.info("Redistributing logins")
        elif task_state == 'Completed':
            logging.info("The state of Redistributing logins task is complete. moving on")
            break
        countdown(0, 20)

    countdown(1, 30)
    tc = "Manual Redistribution of logins"
    logging.info("Check status of manual login redistribution")
    ic_ports_uri_count = ic_inst.get_fc_logins_after(ip, auth, api, enc_name, icm_name_rdl)
    uri_count = (len(ic_ports_uri_count))
    if uri_count == 4:
        result = "Pass"
        logging.info("port count with logins: {}".format(len(ic_ports_uri_count)))
    else:
        result = "Fail"
        logging.warning("port count with logins: {}".format(len(ic_ports_uri_count)))
    PassOrFail(result, tc)

    auto_login_dist_true = 'true'
    link_stab_time = '30'
    logging.info("Setting FC network RDL to Auto with 30 secs wait time.")
    update_net_inst.update_network_rdl_func(ip, auth, api, fc_net_name, link_stab_time, auto_login_dist_true)
    
    countdown(1, 30)
    logging.info("Disabling ports on the ToR")
    cfg_trunk_inst.PersistenDisablePortsTor(tor_ip, tor_un, tor_pw, port_list)

    countdown(2, 30)
    logging.info("Enabling ports on the ToR")
    cfg_trunk_inst.PersistenEnablePortsTor(tor_ip, tor_un, tor_pw, port_list)

    countdown(2 , 0)
    tc = "Auto Redistribution of logins 30 seconds"
    logging.info("Checking logins after 30 second wait time")
    ic_ports_uri_count = ic_inst.get_fc_logins_after(ip, auth, api, enc_name, icm_name_rdl)
    uri_count = (len(ic_ports_uri_count))
    if uri_count == 4:
        result = "Pass"
        logging.info("port count with logins: {}".format(len(ic_ports_uri_count)))
    else:
        result = "Fail"
        logging.warning("port count with logins: {}".format(len(ic_ports_uri_count)))
    PassOrFail(result, tc)

    auto_login_dist = 'true'
    link_stab_time = '60'
    logging.info("Setting FC network RDL to Auto with 60 secs wait time.")
    update_net_inst.update_network_rdl_func(ip, auth, api, fc_net_name, link_stab_time, auto_login_dist)

    countdown(1, 30)
    logging.info("Disabling ports on the ToR")
    cfg_trunk_inst.PersistenDisablePortsTor(tor_ip, tor_un, tor_pw, port_list)

    countdown(2, 30)
    logging.info("Enabling ports on the ToR")
    cfg_trunk_inst.PersistenEnablePortsTor(tor_ip, tor_un, tor_pw, port_list)

    countdown(2 , 30)
    tc = "Auto Redistribution of logins 60 seconds"
    logging.info("Checking logins after 60 second wait time")
    ic_ports_uri_count = ic_inst.get_fc_logins_after(ip, auth, api, enc_name, icm_name_rdl)
    uri_count = (len(ic_ports_uri_count))
    if uri_count == 4:
        result = "Pass"
        logging.info("port count with logins: {}".format(len(ic_ports_uri_count)))
    else:
        result = "Fail"
        logging.warning("port count with logins: {}".format(len(ic_ports_uri_count)))
    PassOrFail(result, tc)


    auto_login_dist = 'true'
    link_stab_time = '30'
    logging.info("Setting FC network RDL to settings prior to test.")
    update_net_inst.update_network_rdl_func(ip, auth, api, fc_net_name, link_stab_time, auto_login_dist)

    countdown(1, 30)
    logging.info("Configuring Trunking on ToR ports.")
    cfg_trunk_inst.EnableTrunkingOnE21TORPort8_11(tor_ip, tor_un, tor_pw)
    
    countdown(1, 0)
    logging.info("Checking final status of FLOGIs, uplink and downlink ports, and state of carbons")
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

    countdown(0, 5)

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

        countdown(3, 0)
        logging.info("Checking to see if carbons are actually turned off")
        tc = "Power turned off on carbon bay1"
        check_carbon_inst.IsCarbonTurnedOffBay1(ip, auth, api, enc_name)
        result = "Pass"
        PassOrFail(result, tc)

        logging.info("Checking to see if carbon in bay1 is in Maintenance State")
        tc = "Carbon in bay1 in Maintenance state"
        mainstate = check_carbon_inst.CheckCarbonMaintenanceStateBay1(ip, auth, api, enc_name)
        print mainstate
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
            countdown(5, 0)
        countdown(3, 0)

        logging.info("Checking to see if carbons are actually turned on")
        tc = "Power turned on carbon bay1"
        check_carbon_inst.IsCarbonTurnedOnBay1(ip, auth, api, enc_name)
        result = "Pass"
        PassOrFail(result, tc)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        get_cbn_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type, enc_name)
        countdown(0, 30)

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

        countdown(3, 0)
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
            print "executing function to efuse for bay4"
            efuse.EfuseCarbon(ip, auth, api, enc_uri, bay)
            countdown(5, 0)
        countdown(3, 0)

        logging.info("Checking to see if carbons are actually turned on")
        tc = "Power turned on carbon bay4"
        check_carbon_inst.IsCarbonTurnedOnBay4(ip, auth, api, enc_name)
        result = "Pass"
        PassOrFail(result, tc)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase, enc_name)
        get_cbn_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type, enc_name)
        counter += 1
        countdown(0, 30)







def main():
    tor_ip = get_tor_ip(ip)
    eagle = get_eagle_enclosure_map(ip)
    setup_logging_Enhanced(eagle, filename)
    auth = get_auth_token()
    get_enc_name_list = Enclosures()
    enc_name = get_enc_name_list.get_enclosure_name(ip, auth, api)
    get_ov_build_carbon_fw_version(auth, enc_name)
    #THIS SECTION OF CODE CONFIGURES EAGLE155
    create_fc_networks(auth)
    ic_types_name_uri = interconnect_type_uri(auth)
    create_lig(auth, ic_types_name_uri)
    lig_uri = get_lig_uri(auth)
    create_enclosure_group(auth, lig_uri)
    enc_grp_uri = get_eg_uri(auth)
    create_le(auth, enc_grp_uri)
    check_le_status(auth)
    create_server_profiles(auth, eagle, enc_grp_uri)
    check_sp_status(auth)
    preflight_check(auth, tor_ip, enc_name)
    #THIS SECTION OF CODE STARTS THE REGRESSION TESTCASES
    icm_uri = get_icm_uri(auth)
    testcase_upload_signed_certs(auth, icm_uri, tor_ip, enc_name)
    testcase_power_off_on_carbon(auth, tor_ip, enc_name)
    testcase_efuse_carbon(auth, tor_ip, enc_name)
    testcase_efuse_carbon_power_off(auth, tor_ip, enc_name)
    testcase_reset_carbon(auth, tor_ip, enc_name)
    testcase_restart_oneview(auth, tor_ip, enc_name)
    testcase_remove_add_fcnetwork_lig(auth, tor_ip, enc_name)
    testcase_icm_utilization(auth, enc_name)
    testcase_remote_syslog(auth, enc_name)
    testcase_connectorinfo_digitaldiag(auth)
    testcase_staticIp_add_remove_encgrp(auth, tor_ip, enc_name)
    testcase_aside_bside_ligs(auth, tor_ip, enc_name)
    testcase_port_mirror(auth, tor_ip, enc_name)
    testcase_remove_add_lig_encgrp(auth, tor_ip, enc_name)
    testcase_portspeed_8_16_32_tor(auth, tor_ip, enc_name)
    testcase_remove_add_fc_network_li(auth, tor_ip, enc_name)
    testcase_update_sp_speeds(auth, eagle, tor_ip, enc_name)
    testcase_redistribute_login(auth, tor_ip, enc_name)
    testcase_carbon_hostname(auth)
    testcase_carbon_connected_to(auth, enc_name)
    testcase_create_le_supportdump(auth, eagle, tor_ip, enc_name)
    testcase_appliance_backup_restore(auth, eagle, tor_ip, enc_name)



if __name__ == '__main__':
    main()
