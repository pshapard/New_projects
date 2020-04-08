"""
/usr/bin/python
Author: Patrick Shapard
created: 07/23/2019
updated: 02/13/2020
This script automates the configuration of an appliance and executes the following testcases.

TestCase: Carbon Failover stress test(multiple iterations)
TestCase: Restart of Oneview (multiple iterations)
TestCase: Carbon Reset stress test
TestCase: Remove/Add FC Network from ULS from LIG (multiple iterations)
TestCase: Remove/Add FC Network from ULS from LI (multiple iterations)
TestCase: UFG LE with A-Side B-side LIGs (multiple iterations)
TestCase: Enable/Disable RemoteSyslog Ipv4 and Ipv6
TestCase: Change port speeds(4/8/16GB) on ToR FC switch
TestCase: Efuse Carbon Stress Test (multiple iterations)
TestCase: Configure Port Monitor, Bi-directional, To Server, From Server
TestCase: Add/Remove IPv4 Static Address Range to/from Enclosure Group
TestCase: Remove/Add LIG from/to Enclosure Group
TestCase: Connector Information and Digital Diagnostics
TestCase: Disable/Enable Trunking on LIG
TestCase: Speed set to 4Gb/8Gb/16Gb with Trunking Enabled
TestCase: Server Profile FC Connection set to 16GB/Auto
TestCase: LIG Port speed change stress test
TestCase: Carbon Utilization Samples
"""
import logging
import sys
import socket
from requests.exceptions import ConnectionError
from SynergyV1400 import AddRemoveUplinkSetsLi
from SynergyV1400 import AddRemoveUplinkSetsLig
from SynergyV1400 import ApplianceSettings
from SynergyV1400 import CheckAllStatesOfCarbon
from SynergyV1400 import CheckStateOfCarbon
from SynergyV1400 import ConfigureTOR
from SynergyV1400 import ConnectorDigDiagInfo
from SynergyV1400 import CreateEnclosureGroup
from SynergyV1400 import CreateFibreChannelNetworks
from SynergyV1400 import CreateLogicalEnclosure
from SynergyV1400 import CreateLogicalInterconnectGroup
from SynergyV1400 import EfuseResource
from SynergyV1400 import Enclosures
from SynergyV1400 import GetCarbonAddressType
from SynergyV1400 import GetCarbonDownLinkPorts
from SynergyV1400 import GetCarbonIp
from SynergyV1400 import GetCarbonPortStatus
from SynergyV1400 import GetCarbonUpLinkPorts  # function
from SynergyV1400 import GetFLOGI
from SynergyV1400 import GetSPStatus
from SynergyV1400 import GetStatusOfLogicalEnclosure
from SynergyV1400 import Interconnects
from SynergyV1400 import LogicalEnclosure
from SynergyV1400 import LogicalInterconnectGroup
from SynergyV1400 import LogicalInterconnects
from SynergyV1400 import LoginCreds
from SynergyV1400 import Networks
from SynergyV1400 import OneViewBuildVersion
from SynergyV1400 import PassOrFail  # function
from SynergyV1400 import PortMonitor
from SynergyV1400 import PowerOffOnServers
from SynergyV1400 import PowerStateOfCarbon
from SynergyV1400 import RemoteSyslog
from SynergyV1400 import ServerProfileBfsLunsNewDTO
from SynergyV1400 import ServerProfileConnectionSpeeds
from SynergyV1400 import Servers
from SynergyV1400 import StateOfEnclosure
from SynergyV1400 import UpdateEnclosureGroup as UpdateEG
from SynergyV1400 import UpdateLogicalEnclosure
from SynergyV1400 import UpdateLogicalInterconnectGroup
from SynergyV1400 import UpdateLogicalInterconnects
from SynergyV1400 import UpdateServerProfileBfsLunsNewDTO
from SynergyV1400 import countdown  # function
from SynergyV1400 import get_eagle_enclosure_map
from SynergyV1400 import get_tor_ip
from SynergyV1400 import printDict  # function
from SynergyV1400 import setup_logging_Enhanced
from SynergyV1400 import sshclient

ip = ['appliance ip']

filename = 'Eagle21TestSuiteSynergyV1400._5.20.82'
# Global variables
fc_mode = "TRUNK"
v3_enabled = "true"
consistency_check = "ExactMatch"
number = 1


def check_cim_ready():
    # While loop to check if the CIM is ready to receive login requests
    count = 0
    while True:
        cmd = 'ls -l'
        try:
            sshclient(ip, user, cim_pw, cmd)
            print "The CIM is ready for login requests, moving on"
            break
        except socket.error as e:
            print "The CIM is not ready for login requests"
        count = count + 1
        if count == 20:
            print "Unable to connect to the CIM, quitting script"
            sys.exit(0)
        else:
            pass
        countdown(1, 0)


def get_AT():
    login_inst = LoginCreds()
    try:
        auth = login_inst.LoginToken(ip, api, username, password)
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
    logging.testcases("The OneView version/build is: {}".format(version))
    logging.testcases("The ip address of this enclosure is: {}".format(ip))
    logging.testcases("The carbon fw version is: {}".format(carbon_fw))


def create_fc_networks(auth):
    fibre_channel_network = ('BAY1', 'BAY4', 'BAY1-Q1-PORTS')
    for net in fibre_channel_network:
        logging.info("Creating {} network".format(net))
        fc_networks_inst = CreateFibreChannelNetworks()
        fc_networks_inst.CreateFcNetwork(ip, auth, api, net)


def get_enclosure_uri(auth):
    logging.info("Getting Enclosures ")
    enclosure_inst = Enclosures()
    enc_dict = enclosure_inst.GetEnc(ip, auth, api)
    enclosure_uri = printDict(enc_dict, ['uri'])
    enc_uri = enclosure_uri[0]['uri']
    return enc_uri


def interconnect_type_uri(auth):
    logging.info("Getting interconnect types uri")
    interconnect_types_inst = Interconnects()
    ic_types = interconnect_types_inst.GetInterconnectTypes(ip, auth, api)
    ic_types_uri = printDict(ic_types, ['uri'])
    ic_types_name = printDict(ic_types, ['name'])
    return ic_types_uri, ic_types_name


def create_lig(auth, ic_types_uri, ic_types_name):
    retrieve_net_inst = Networks()
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle21(
        ip, auth, api)
    logging.info("Creating a LIG")
    for s, value in enumerate(ic_types_uri):
        ic_type_uri = ic_types_uri[s]['uri']
        ic_name = ic_types_name[s]['name']
        if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
            create_lig_inst = CreateLogicalInterconnectGroup()
            create_lig_inst.CreateLigE21(ip, auth, api, ic_type_uri, fc_mode, v3_enabled, fc_net_enc1_bay1_uri,
                                             fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, consistency_check)
    logging.info("Pausing for 30 secs for LIGs to be created")
    countdown(0, 30)


def get_lig_uri(auth):
    ligs_inst = LogicalInterconnectGroup()
    list_of_lig = ligs_inst.GetListOfLIGs(ip, auth, api)
    lig_uri_list = printDict(list_of_lig, ['uri'])
    lig_uri = lig_uri_list[0]['uri']
    return lig_uri


def create_enclosure_group(auth, lig_uri):
    create_eg_inst = CreateEnclosureGroup()
    create_eg_inst.CreateEgTBird(ip, auth, api, lig_uri)
    logging.info("Pausing for 30 secs for EG to be created")
    countdown(0, 30)


def get_eg_uri(auth):
    logging.info("Getting Enclosure Group ")
    enc_inst = Enclosures()
    enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
    encl_group_uri_list = printDict(enc_grp_dict, ['uri'])
    enc_grp_uri = encl_group_uri_list[0]['uri']
    return enc_grp_uri


def create_le(auth, enc_uri, enc_grp_uri):
    logging.info("Creating Logical Enclosure")
    create_log_enc_inst = CreateLogicalEnclosure()
    create_log_enc_inst.CreateLE(ip, auth, api, enc_uri, enc_grp_uri)
    logging.info("Pausing for 8 mins.  Waiting for LE to be created")
    countdown(8, 0)


def check_le_status(auth):
    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)


def create_server_profiles(auth, eagle, enc_grp_uri):
    retrieve_net_inst = Networks()
    server_hw_profile_inst = Servers()
    create_sp_inst = ServerProfileBfsLunsNewDTO()
    power_cycle_server_inst = PowerOffOnServers()
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle21(
        ip, auth, api)
    logging.info("Getting Server HW and Profiles")
    array_wwpn1, array_wwpn2, wwnn1_start, wwpn1_start, wwnn2_start, wwpn2_start = server_hw_profile_inst.server_wwnn_start_wwpn_start(
        eagle)
    sp_name, sp_descr, id_1, id_2 = server_hw_profile_inst.server_profile_config()
    wwnn1, wwpn1, wwnn2, wwpn2 = server_hw_profile_inst.server_wwwn_wwpn(wwnn1_start, wwpn1_start, wwnn2_start,
                                                                         wwpn2_start)
    server_hw_list = server_hw_profile_inst.ServerHW(ip, auth, api)
    server_hw_names_dict = printDict(server_hw_list, ['name', 'uri', 'model', 'serialNumber'])
    shw_dict_sorted = sorted(server_hw_names_dict)

    power_cycle_server_inst.power_off_servers(ip, auth, api)
    mode = "UEFI"

    logging.info("starting Server HW list loop to create server profiles")
    for i, value in enumerate(shw_dict_sorted):
        server_hw_uri = shw_dict_sorted[i]['uri']
        server_name = shw_dict_sorted[i]['name']
        server_sn = shw_dict_sorted[i]['serialNumber']
        logging.info("Creating {} for server {} sn: {}".format(sp_name[i], server_name, server_sn))
        if server_sn == "MXQ915012D" or server_sn == "MXQ915012Q" or server_sn == "MXQ915012M":
            create_sp_inst.CreateServerProfileBootFromSAN(ip, auth, api, sp_name[i], server_hw_uri, enc_grp_uri,
                                                          sp_descr[i], fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri,
                                                          id_1[i], id_2[i], wwnn1[i], wwpn1[i], array_wwpn1, wwnn2[i],
                                                          wwpn2[i], array_wwpn2, mode)
        elif server_sn == "MXQ81806JK":
            create_sp_inst.CreateServerProfileLuns(ip, auth, api, sp_name[i], server_hw_uri, enc_grp_uri, sp_descr[i],
                                                   fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, id_1[i], id_2[i],
                                                   wwnn1[i], wwpn1[i], wwnn2[i], wwpn2[i], mode)
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
    PassOrFail(result, tc)
    power_cycle_server_inst = PowerOffOnServers()
    power_cycle_server_inst.power_on_servers(ip, auth, api)
    countdown(3, 0)
    power_cycle_server_inst.check_server_power(ip, auth, api)


def preflight_check(auth, tor_ip):
    logging.info("Checking state of carbons before starting testsuite")
    check_carbon_inst = CheckStateOfCarbon()
    check_carbon_inst.CheckCarbonForErrors(ip, auth, api)
    check_carbon_inst.CheckCarbonState(ip, auth, api)
    get_num_flogi_inst = GetFLOGI()
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)


##################################REGRESSION TESTSUITE STARTS HERE####################################################################################

def testcase_power_off_on_carbon(auth, tor_ip):
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
    counter = 0
    logging.info("Checking the status of the downlink and uplink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    all_states_inst = CheckAllStatesOfCarbon()
    check_carbon_inst = CheckStateOfCarbon()
    get_num_flogi_inst = GetFLOGI()

    logging.info("Getting Interconnects")
    ic_inst = Interconnects()
    get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
    ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])

    countdown(0, 5)

    # While loop to turn off and on carbon ICMs
    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        # For loop to interate thru carbon bay4 and power it off
        logging.info("Power off the carbon ICMs in bay4")
        for ic, value in enumerate(ic_name_uri_list):
            ic_uri = ic_name_uri_list[ic]['uri']
            ic_name = ic_name_uri_list[ic]['name']
            enc_name = ic_name_uri_list[ic]['enclosureName']
            carbon_power_inst = PowerStateOfCarbon()
            if ic_name == "{}, interconnect 4".format(enc_name):
                logging.info("Powering off the carbon in {}".format(ic_name))
                carbon_power_inst.PowerOffCarbon(ip, auth, api, ic_uri)
            else:
                pass

        countdown(2, 0)
        logging.info("Checking to see if carbons are actually turned off")
        tc = "Power turned off on carbon bay4"
        check_carbon_inst.IsCarbonTurnedOffBay4(ip, auth, api)
        result = "Pass"
        PassOrFail(result, tc)

        countdown(3, 0)
        # For loop to interate thru carbon ICM in Bay4 and power it On
        for ic, value in enumerate(ic_name_uri_list):
            ic_uri = ic_name_uri_list[ic]['uri']
            ic_name = ic_name_uri_list[ic]['name']
            enc_name = ic_name_uri_list[ic]['enclosureName']
            if ic_name == "{}, interconnect 4".format(enc_name):
                logging.info("Powering on the carbon in {}".format(ic_name))
                carbon_power_inst.PowerOnCarbon(ip, auth, api, ic_uri)
            else:
                logging.info("The power on function did not execute")
                pass

        countdown(7, 0)
        logging.info("Checking to see if carbons are actually turned on")
        tc = "Power turned on carbon bay4"
        check_carbon_inst.IsCarbonTurnedOnBay4(ip, auth, api)
        result = "Pass"
        PassOrFail(result, tc)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase)

        # For loop to iterate thru carbon bay1 and power it off
        logging.info("Power off the carbon ICMs in bay1")
        for ic, value in enumerate(ic_name_uri_list):
            ic_uri = ic_name_uri_list[ic]['uri']
            ic_name = ic_name_uri_list[ic]['name']
            enc_name = ic_name_uri_list[ic]['enclosureName']
            if ic_name == "{}, interconnect 1".format(enc_name):
                logging.info("Powering off the carbon in {}".format(ic_name))
                carbon_power_inst.PowerOffCarbon(ip, auth, api, ic_uri)
            else:
                pass

        countdown(2, 0)

        logging.info("Checking to see if carbons are actually turned off")
        tc = "Power turned off on carbon bay1"
        check_carbon_inst.IsCarbonTurnedOffBay1(ip, auth, api)
        result = "Pass"
        PassOrFail(result, tc)

        countdown(3, 0)
        # For loop to interate thru carbon in bay1 and power it On
        for ic, value in enumerate(ic_name_uri_list):
            ic_uri = ic_name_uri_list[ic]['uri']
            ic_name = ic_name_uri_list[ic]['name']
            enc_name = ic_name_uri_list[ic]['enclosureName']
            if ic_name == "{}, interconnect 1".format(enc_name):
                logging.info("Powering on the carbon in {}".format(ic_name))
                carbon_power_inst.PowerOnCarbon(ip, auth, api, ic_uri)
            else:
                pass
        countdown(7, 0)
        logging.info("Checking to see if carbons are actually turned on")
        tc = "Power turned on carbon bay1"
        check_carbon_inst.IsCarbonTurnedOnBay1(ip, auth, api)
        result = "Pass"
        PassOrFail(result, tc)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        counter += 1
        countdown(0, 30)
        logging.info("Starting next iteration")


def testcase_efuse_carbon(auth, tor_ip):
    # This test case efuses carbon in bays1 and 4, waits 6 mins, then checks the if carbons are in error state, other than configured state,
    # then checks the status of the uplink and downlink ports.
    logging.testcases("##################################")
    logging.testcases("TestCase: Carbon Efuse stress test")
    logging.testcases("##################################")
    testcase = 'Carbon Efuse stress test'
    addr_type = "dhcp"
    logging.info("Checking the status of the downlink and uplink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    # Create Instances of Classes used in this script
    check_carbon_inst = CheckStateOfCarbon()
    efuse = EfuseResource()
    all_states_inst = CheckAllStatesOfCarbon()
    get_addr_type_inst = GetCarbonAddressType()
    get_num_flogi_inst = GetFLOGI()

    counter = 0

    logging.info("Getting Enclosures ")
    enc_inst = Enclosures()
    enc_dict = enc_inst.GetEnc(ip, auth, api)
    enc_uri_list = printDict(enc_dict, ['uri'])

    countdown(0, 5)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Efusing carbon in Bay1")
        for i, value in enumerate(enc_uri_list):
            enc_uri = enc_uri_list[i]['uri']
            bay = "1"
            efuse.EfuseCarbon(ip, auth, api, enc_uri, bay)
            countdown(5, 0)
        countdown(1, 0)

        logging.info("Checking to see if carbons are actually turned on")
        tc = "Power turned on carbon bay1"
        check_carbon_inst.IsCarbonTurnedOnBay1(ip, auth, api)
        result = "Pass"
        PassOrFail(result, tc)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        get_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type)
        countdown(0, 30)
        logging.info("Now will efuse carbon in bay4")
        logging.info("Efusing carbon in Bay4")
        for i, value in enumerate(enc_uri_list):
            enc_uri = enc_uri_list[i]['uri']
            bay = "4"
            print "executing function to efuse for bay4"
            efuse.EfuseCarbon(ip, auth, api, enc_uri, bay)
            countdown(5, 0)
        countdown(1, 0)

        logging.info("Checking to see if carbons are actually turned on")
        tc = "Power turned on carbon bay4"
        check_carbon_inst.IsCarbonTurnedOnBay4(ip, auth, api)
        result = "Pass"
        PassOrFail(result, tc)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        get_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type)
        counter += 1
        countdown(1, 0)


def testcase_efuse_carbon_power_off(auth, tor_ip):
    # This test case efuses carbon in bays1 and 4, waits 6 mins, then checks the if carbons are in error state, other than configured state,
    # then checks the status of the uplink and downlink ports.
    logging.testcases("#################################################")
    logging.testcases("TestCase: Carbon Efuse stress test with power off")
    logging.testcases("#################################################")
    testcase = 'Carbon Efuse stress test'
    addr_type = "dhcp"
    counter = 0
    logging.info("Checking the status of the downlink and uplink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    # Create Instances of Classes used in this script
    check_carbon_inst = CheckStateOfCarbon()
    efuse = EfuseResource()
    all_states_inst = CheckAllStatesOfCarbon()
    get_addr_type_inst = GetCarbonAddressType()
    get_num_flogi_inst = GetFLOGI()

    logging.info("Getting Interconnects")
    ic_inst = Interconnects()
    get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
    ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])

    logging.info("Getting Enclosures ")
    enc_inst = Enclosures()
    enc_dict = enc_inst.GetEnc(ip, auth, api)
    enc_uri_list = printDict(enc_dict, ['uri'])

    countdown(0, 5)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        # For loop to iterate thru carbon bay1 and power it off
        logging.info("Power off the carbon ICMs in bay1")
        for ic, value in enumerate(ic_name_uri_list):
            ic_uri = ic_name_uri_list[ic]['uri']
            ic_name = ic_name_uri_list[ic]['name']
            enc_name = ic_name_uri_list[ic]['enclosureName']
            carbon_power_inst = PowerStateOfCarbon()
            if ic_name == "{}, interconnect 1".format(enc_name):
                logging.info("Powering off the carbon in {}".format(ic_name))
                carbon_power_inst.PowerOffCarbon(ip, auth, api, ic_uri)
            else:
                pass

        countdown(3, 0)
        logging.info("Checking to see if carbons are actually turned off")
        tc = "Power turned off on carbon bay1"
        check_carbon_inst.IsCarbonTurnedOffBay1(ip, auth, api)
        result = "Pass"
        PassOrFail(result, tc)

        logging.info("Checking to see if carbon in bay1 is in Maintenance State")
        tc = "Carbon in bay1 in Maintenance state"
        mainstate = check_carbon_inst.CheckCarbonMaintenanceStateBay1(ip, auth, api)
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
        check_carbon_inst.IsCarbonTurnedOnBay1(ip, auth, api)
        result = "Pass"
        PassOrFail(result, tc)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        get_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type)
        countdown(0, 30)

        # For loop to interate thru carbon bay4 and power it off
        logging.info("Power off the carbon ICMs in bay4")
        for ic, value in enumerate(ic_name_uri_list):
            ic_uri = ic_name_uri_list[ic]['uri']
            ic_name = ic_name_uri_list[ic]['name']
            enc_name = ic_name_uri_list[ic]['enclosureName']
            carbon_power_inst = PowerStateOfCarbon()
            if ic_name == "{}, interconnect 4".format(enc_name):
                logging.info("Powering off the carbon in {}".format(ic_name))
                carbon_power_inst.PowerOffCarbon(ip, auth, api, ic_uri)
            else:
                pass

        countdown(3, 0)
        logging.info("Checking to see if carbons are actually turned off")
        tc = "Power turned off on carbon bay4"
        check_carbon_inst.IsCarbonTurnedOffBay4(ip, auth, api)
        result = "Pass"
        PassOrFail(result, tc)

        logging.info("Checking to see if carbon in bay4 is in Maintenance State")
        tc = "Carbon in bay4 in Maintenance state"
        mainstate = check_carbon_inst.CheckCarbonMaintenanceStateBay4(ip, auth, api)
        print mainstate
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
        check_carbon_inst.IsCarbonTurnedOnBay4(ip, auth, api)
        result = "Pass"
        PassOrFail(result, tc)

        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        get_addr_type_inst.GetCarbonIPAddressType(ip, auth, api, addr_type)
        counter += 1
        countdown(0, 30)


def testcase_restart_oneview(auth, tor_ip):
    logging.testcases("############################")
    logging.testcases("TestCase: Restart of Oneview")
    logging.testcases("############################")

    testcase = 'Restart of Oneview'
    logging.info("Checking the status of the downlink and uplink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    # instantiation of Classes
    all_states_inst = CheckAllStatesOfCarbon()
    state_of_enc = StateOfEnclosure()
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
        auth = login.LoginToken(ip, api, username, password)

        # try:
        refresh_state = state_of_enc.EncRefreshState(ip, auth, api)
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
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        counter += 1


def testcase_icm_utilization(auth):
    logging.testcases("#####################################")
    logging.testcases("TestCase: Carbon Utilization Samples")
    logging.testcases("#####################################")
    icm_util = Interconnects()
    icm_util.get_carbon_utilization(ip, auth, api)


def testcase_remote_syslog(auth):
    logging.testcases("###################################################")
    logging.testcases("TestCase: Enable/Disable RemoteSyslog Ipv4 and Ipv6")
    logging.testcases("###################################################")

    testcase = 'Enable/Disable RemoteSyslog Ipv4 and Ipv6'
    result = None
    logging.info("Checking the status of the downlink and uplink ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    countdown(0, 5)

    tc = "Enable RemoteSyslog Ipv6"
    remote_syslog_inst = RemoteSyslog()

    logging.info("Enable remote Syslog with IPv6 address")
    remote_syslog_inst.EnableRemoteSyslogIPv6(ip, auth, api)
    countdown(3, 0)
    all_states_inst = CheckAllStatesOfCarbon()
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)

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
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
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
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
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
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
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


def testcase_staticIp_add_remove_encgrp(auth, tor_ip):
    logging.testcases("######################################################################")
    logging.testcases("TestCase: Add/Remove IPv4 Static Address Range to/from Enclosure Group")
    logging.testcases("######################################################################")

    testcase = 'Add/Remove IPv4 Static Address Range to/from Enclosure Group'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    countdown(0, 5)

    all_states_inst = CheckAllStatesOfCarbon()
    ipv4_settings_inst = ApplianceSettings()
    carbon_ipAddr_type_inst = GetCarbonIp()
    get_num_flogi_inst = GetFLOGI()

    logging.info("Getting Enclosure Group ")
    enc_inst = Enclosures()
    enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
    enc_grp_list = printDict(enc_grp_dict, ['name', 'uri', 'eTag'])
    enc_grp_uri = enc_grp_list[0]['uri']
    enc_grp_etag = enc_grp_list[0]['eTag']

    logging.info("Getting Enclosures ")
    enc_dict = enc_inst.GetEnc(ip, auth, api)

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

    ipv4_settings_inst.CreateIPv4Subnet(ip, auth, api)
    logging.info("Getting ipv4 subnet")
    get_subnet = ipv4_settings_inst.GetIPv4Subnet(ip, auth, api)
    subnet_list = printDict(get_subnet, ['uri'])
    subnet_uri = subnet_list[0]['uri']
    logging.info("Creating ipv4 address range")
    ipv4_settings_inst.CreateIPv4Range(ip, auth, api, subnet_uri)
    countdown(0, 2)
    get_subnet = ipv4_settings_inst.GetIPv4Subnet(ip, auth, api)
    IPv4Range = printDict(get_subnet, ['rangeUris'])
    RangeListDict = IPv4Range[0]['rangeUris']
    range_uri = RangeListDict[0]
    logging.info("Updating Enclosure Group with Static IPv4 address range")
    update_enc_grp_inst.UpdateEGIPv4RangeE21(ip, auth, api, enc_grp_uri, enc_grp_etag, range_uri, lig1_uri)

    countdown(0, 30)
    logging.info("*******************UPDATING LE ***************************")

    logging.info("Getting Logical Enclosure")
    le_inst = LogicalEnclosure()
    le_dict = le_inst.GetLogicalEnclosure(ip, auth, api)
    le_uri_list = printDict(le_dict, ['uri'])
    LeUri = le_uri_list[0]['uri']

    logging.info("Updating LE from group")
    update_le_inst = UpdateLogicalEnclosure()
    update_le_inst.LeUpdateFromGroup(ip, auth, api, LeUri)

    logging.info("Pausing for 15mins to wait for the LE to updated from group")
    countdown(15, 0)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)

    logging.info("*******************CHECKING IP ADDRESS TYPE OF CARBONS***************************")
    logging.info("Getting Enclosures")
    enc_dict = enc_inst.GetEnc(ip, auth, api)
    enclosure_name = printDict(enc_dict, ['name'])
    enc_name = enclosure_name[0]['name']

    logging.info("Getting the ip type of carbons")
    tc = "Carbon in bay1 has static ip IPv4 address"
    carbon_bay1_ip_type = carbon_ipAddr_type_inst.GetIPTypeCarbonOneME(ip, api, auth, enc_name)
    logging.info("{}".format(carbon_bay1_ip_type))
    if carbon_bay1_ip_type == "Ipv4Static":
        result = "Pass"
        PassOrFail(result, tc)
    elif carbon_bay1_ip_type == "Ipv4Dhcp":
        result = "Fail"
        PassOrFail(result, tc)

    tc = "Carbon in bay4 has static ip IPv4 address"
    carbon_bay4_ip_type = carbon_ipAddr_type_inst.GetIPTypeCarbonFourME(ip, api, auth, enc_name)
    logging.info("{}".format(carbon_bay4_ip_type))
    if carbon_bay4_ip_type == "Ipv4Static":
        result = "Pass"
        PassOrFail(result, tc)
    elif carbon_bay4_ip_type == "Ipv4Dhcp":
        result = "Fail"
        PassOrFail(result, tc)

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
    update_le_inst.LeUpdateFromGroup(ip, auth, api, LeUri)

    logging.info("********************UPDATE FROM GROUP THE LE***************************")

    logging.info("Pausing for 10mins for LE to be updated from group")
    countdown(10, 0)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)

    logging.info("*******************CHECKING IP ADDRESS TYPE OF CARBONS***************************")
    logging.info("Getting the ip type of carbons")
    tc = "Carbon in bay1 has dhcp ip IPv4 address"
    carbon_bay1_ip_type = carbon_ipAddr_type_inst.GetIPTypeCarbonOneME(ip, api, auth, enc_name)
    logging.info("{}".format(carbon_bay1_ip_type))
    if carbon_bay1_ip_type == "Ipv4Dhcp":
        result = "Pass"
        PassOrFail(result, tc)
    elif carbon_bay1_ip_type == "Ipv4Static":
        result = "Fail"
        PassOrFail(result, tc)
    elif carbon_bay1_ip_type == "None":
        result = "Fail"
        PassOrFail(result, tc)

    tc = "Carbon in bay4 has dhcp ip IPv4 address"
    carbon_bay4_ip_type = carbon_ipAddr_type_inst.GetIPTypeCarbonFourME(ip, api, auth, enc_name)
    logging.info("{}".format(carbon_bay4_ip_type))
    if carbon_bay4_ip_type == "Ipv4Dhcp":
        result = "Pass"
        PassOrFail(result, tc)
    elif carbon_bay4_ip_type == "Ipv4Static":
        result = "Fail"
        PassOrFail(result, tc)
    elif carbon_bay4_ip_type == "None":
        result = "Fail"
        PassOrFail(result, tc)


def testcase_remove_add_fc_network_lig(auth, tor_ip):
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

    testcase = 'Remove/Add FC Network from ULS from LIG'
    counter = 0

    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()
    retrieve_net_inst = Networks()
    countdown(0, 2)

    logging.info("Getting interconnect types uri")
    ic_types_dict = Interconnects()
    ic_types_list = ic_types_dict.GetInterconnectTypes(ip, auth, api)
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
        for i, value in enumerate(ligs_name_uri):
            lig_name = ligs_name_uri[i]['name']
            if lig_name == "LIG":
                lig_uri = ligs_name_uri[i]['uri']
        for s, value in enumerate(ic_types_name_uri):
            ic_type_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                uplink_sets_inst = AddRemoveUplinkSetsLig()
                uplink_sets_inst.RemoveBay1FcNetworkLig(ip, auth, api, ic_type_uri, fc_net_enc1_bay1_quri,
                                                        fc_net_enc1_bay4_uri, lig_uri, consistency_check)

        countdown(0, 15)

        logging.info("Getting Logical Interconnects")
        li_inst = LogicalInterconnects()
        li_list = li_inst.GetLogicalInterconnects(ip, auth, api)
        li_name_uri = printDict(li_list, ['uri', 'name'])

        logging.info("Updating LI from group")
        for i, value in enumerate(li_name_uri):
            logging.info("Updating {} from LIG".format(li_name_uri[i]['name']))
            li_uri = li_name_uri[i]['uri']
            update_li_inst = UpdateLogicalInterconnects()
            update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

        countdown(10, 0)

        for s, value in enumerate(ic_types_name_uri):
            ic_type_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                uplink_sets_inst.AddBay1Bay4FcNetworkLig(ip, auth, api, ic_type_uri, fc_net_enc1_bay1_uri,
                                                         fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, lig_uri,
                                                         consistency_check)

        countdown(0, 15)

        logging.info("Updating LI from group")
        for i, value in enumerate(li_name_uri):
            logging.info("Updating {} from LIG".format(li_name_uri[i]['name']))
            li_uri = li_name_uri[i]['uri']
            update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)
            logging.info("Pausing for 7mins before checking state and downlink ports on carbons")

        countdown(7, 0)

        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        logging.info("Getting the number of FLOGIs")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

        for s, value in enumerate(ic_types_name_uri):
            ic_type_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                uplink_sets_inst.RemoveBay4FcNetworkLig(ip, auth, api, ic_type_uri, fc_net_enc1_bay1_uri,
                                                        fc_net_enc1_bay1_quri, lig_uri, consistency_check)

        countdown(0, 30)

        logging.info("Updating LI from group")
        for i, value in enumerate(li_name_uri):
            logging.info("Updating {} from LIG".format(li_name_uri[i]['name']))
            li_uri = li_name_uri[i]['uri']
            update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

        countdown(7, 0)

        for s, value in enumerate(ic_types_name_uri):
            ic_type_uri = ic_types_name_uri[s]['uri']
            ic_name = ic_types_name_uri[s]['name']
            if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                uplink_sets_inst.AddBay1Bay4FcNetworkLig(ip, auth, api, ic_type_uri, fc_net_enc1_bay1_uri,
                                                         fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, lig_uri,
                                                         consistency_check)

        countdown(0, 30)

        logging.info("Getting Logical Interconnects")
        li_list = li_inst.GetLogicalInterconnects(ip, auth, api)
        li_name_uri = printDict(li_list, ['uri', 'name'])

        logging.info("Updating LI from group.")
        for i, value in enumerate(li_name_uri):
            logging.info("Updating {} from LIG".format(li_name_uri[i]['name']))
            li_uri = li_name_uri[i]['uri']
            update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

        countdown(10, 0)

        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        logging.info("Getting the number of FLOGIs")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

        counter += 1
        countdown(0, 10)


def testcase_remove_add_fc_network_li(auth, tor_ip):
    logging.testcases("################################################")
    logging.testcases("TestCase: Remove/Add FC Network from ULS from LI")
    logging.testcases("################################################")

    testcase = 'Remove/Add FC Network from ULS from LI'
    counter = 0
    # Check UL and DL port status on both carbons before starting test
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    all_states_inst = CheckAllStatesOfCarbon()
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

    uplink_sets_inst = AddRemoveUplinkSetsLi()
    countdown(0, 10)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Removing FC network from Bay1 Uplink Set")
        uplink_sets_inst.RemoveUlsBay1FcNetworkLi(ip, auth, api, li_uri, enc_uri, uls_bay1_uri)
        countdown(5, 0)

        logging.info("Adding FC network to Bay1 Uplink Set")
        uplink_sets_inst.AddUlsBay1FcNetworkLi(ip, auth, api, fc_net_enc1_bay1_uri, li_uri, enc_uri, uls_bay1_uri)
        countdown(7, 0)

        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        logging.info("Getting the number of FLOGIs")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

        logging.info("Removing FC network from Bay4 Uplink Set")
        uplink_sets_inst.RemoveUlsBay4FcNetworkLi(ip, auth, api, li_uri, enc_uri, uls_bay4_uri)
        countdown(5, 0)

        logging.info("Adding FC network to Bay4 Uplink Set")
        uplink_sets_inst.AddUlsBay4FcNetworkLi(ip, auth, api, fc_net_enc1_bay4_uri, li_uri, enc_uri, uls_bay4_uri)
        countdown(7, 0)

        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        logging.info("Getting the number of FLOGIs")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

        counter += 1
        countdown(0, 30)


def testcase_aside_bside_ligs(auth, tor_ip):
    logging.testcases("########################################")
    logging.testcases("TestCase: UFG LE with A-Side B-side LIGs")
    logging.testcases("########################################")

    testcase = 'UFG LE with A-Side B-side LIGs'
    counter = 0

    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    countdown(0, 5)

    # instantiation of Classes
    all_states_inst = CheckAllStatesOfCarbon()
    power_cycle_server_inst = PowerOffOnServers()
    retrieve_net_inst = Networks()
    get_num_flogi_inst = GetFLOGI()

    logging.info("*******************CREATING A-SIDE AND B-SIDE LIGs ***************************")

    logging.info("Getting interconnect types uri")
    ic_types_dict = Interconnects()
    ic_types_list = ic_types_dict.GetInterconnectTypes(ip, auth, api)
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
                if ic_name == "Virtual Connect SE 16Gb FC Module for Synergy":
                    create_lig_inst = CreateLogicalInterconnectGroup()
                    create_lig_inst.CreateLigASideE21Trunk(ip, auth, api, ic_uri, fc_mode, v3_enabled,
                                                           fc_net_enc1_bay1_uri, fc_net_enc1_bay1_quri)
                    create_lig_inst.CreateLigBSideE21Trunk(ip, auth, api, ic_uri, fc_mode, v3_enabled,
                                                           fc_net_enc1_bay4_uri)
            logging.info("Pausing 20 secs for the LIGs to be created")
            countdown(0, 20)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Getting list of LIGs")
        ligs_inst = LogicalInterconnectGroup()
        ligs_list = ligs_inst.GetListOfLIGs(ip, auth, api)
        ligs_name_uri = printDict(ligs_list, ['name', 'uri'])

        logging.info("Getting Enclosure Group ")
        enc_inst = Enclosures()
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

        logging.info("*******************UPDATING EG ***************************")

        update_enc_grp_inst = UpdateEG()
        update_enc_grp_inst.UpdateEgE21(ip, auth, api, enc_grp_uri, enc_grp_etag, lig1_uri, lig2_uri)

        logging.info("Pausing for 30 secs for EG to be updated")
        countdown(0, 30)

        logging.info("Pausing for 3mins to power off servers")
        power_cycle_server_inst.power_off_servers(ip, auth, api)
        countdown(1, 0)

        logging.info("*******************UPDATING LE ***************************")

        logging.info("Getting Logical Enclosure")
        le_dict = LogicalEnclosure()
        le_list = le_dict.GetLogicalEnclosure(ip, auth, api)
        le_uri_list = printDict(le_list, ['uri'])
        LeUri = le_uri_list[0]['uri']

        logging.info("Updating LE from group")
        update_le = UpdateLogicalEnclosure()
        update_le.LeUpdateFromGroup(ip, auth, api, LeUri)

        logging.info("Pausing for 10mins to wait for the LE to updated from group")
        countdown(10, 0)

        logging.info("Checking status of LE")
        GetStatusOfLogicalEnclosure(ip, auth, api)

        logging.info("Pausing for 7mins to power on servers")
        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(7, 0)

        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

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

        logging.info("Pausing for 3mins to power off servers")
        power_cycle_server_inst.power_off_servers(ip, auth, api)
        countdown(1, 0)

        logging.info("Updating LE from group")
        update_le.LeUpdateFromGroup(ip, auth, api, LeUri)

        logging.info("********************UPDATE FROM GROUP THE LE***************************")

        logging.info("Pausing for 10mins for LE to be updated from group")
        countdown(10, 0)

        logging.info("Checking status of LE")
        GetStatusOfLogicalEnclosure(ip, auth, api)

        logging.info("Pausing for 7mins to power on servers")
        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(7, 0)

        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

        counter += 1
        countdown(1, 0)


def testcase_portspeed_4_8_16_tor(auth, tor_ip):
    logging.testcases("#######################################################")
    logging.testcases("TestCase: Change port speeds(4/8/16GB) on ToR FC switch")
    logging.testcases("#######################################################")

    testcase = 'Change port speeds(4/8/16GB) on ToR FC switch'
    logging.info("Checking the status of the downlink and uplink ports before starting the test")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    port_speed_inst = ConfigureTOR()
    carbon_port_speed_inst = GetCarbonPortStatus()
    get_num_flogi_inst = GetFLOGI()
    all_states_inst = CheckAllStatesOfCarbon()
    countdown(0, 10)

    logging.testcases("Port speed set to 4Gb")
    port_speed_inst.ConfigPortSpeed4GbE21TORPort16_19(tor_ip, tor_un, tor_pw)
    countdown(5, 0)
    carbon_port_speed_inst.GetCarbonUpLinkPortSpeed4Gb(ip, api, auth)

    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
    logging.info("Getting the number of FLOGIs")
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

    logging.testcases("Port speed set to 8Gb")
    port_speed_inst.ConfigPortSpeed8GbE21TORPort16_19(tor_ip, tor_un, tor_pw)
    countdown(5, 0)
    carbon_port_speed_inst.GetCarbonUpLinkPortSpeed8Gb(ip, api, auth)

    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
    logging.info("Getting the number of FLOGIs")
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

    logging.testcases("Port speed set to 16Gb")
    port_speed_inst.ConfigPortSpeed16GbE21TORPort16_19(tor_ip, tor_un, tor_pw)
    countdown(5, 0)
    carbon_port_speed_inst.GetCarbonUpLinkPortSpeed16Gb(ip, api, auth)

    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
    logging.info("Getting the number of FLOGIs")
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

    logging.testcases("Port speed set to Auto")
    port_speed_inst.ConfigPortSpeedAutobE21TORPort16_19(tor_ip, tor_un, tor_pw)
    countdown(5, 0)
    carbon_port_speed_inst.GetCarbonUpLinkPortSpeed16Gb(ip, api, auth)

    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
    logging.info("Getting the number of FLOGIs")
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)


def testcase_port_mirror(auth, tor_ip):
    logging.testcases("########################################################################")
    logging.testcases("TestCase: Configure Port Monitor, Bi-directional, To Server, From Server")
    logging.testcases("########################################################################")

    testcase = 'Configure Port Monitor, Bi-directional, To Server, From Server'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()
    logging.info("Getting Interconnects")
    ic_inst = Interconnects()
    get_ic_list = ic_inst.GetInterconnect(ip, auth, api)
    ic_name_uri_list = printDict(get_ic_list, ['productName', 'name', 'ports', 'enclosureName'])

    logging.info("Getting list of DL and UL ports to use for port monitor")
    for i, value in enumerate(ic_name_uri_list):
        ports_list = ic_name_uri_list[i]['ports']
        ic_name = ic_name_uri_list[i]['name']
        enc_name = ic_name_uri_list[i]['enclosureName']
        if ic_name == "{}, interconnect 1".format(enc_name):
            for p in range(0, len(ports_list)):
                port_name = ports_list[p]['portName']
                port_uri = ports_list[p]['uri']
                if port_name == "5":
                    ul_port_uri = port_uri
                if port_name == "d1":
                    dl_port_uri = port_uri

    # logging.info("Getting list of logical interconnects")
    logging.info("Getting Logical Interconnects")
    get_li_dict = LogicalInterconnects()
    li_list = get_li_dict.GetLogicalInterconnects(ip, auth, api)
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

    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
    logging.info("Getting the number of FLOGIs")
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)


def testcase_remove_add_lig_encgrp(auth, tor_ip):
    logging.testcases("################################################")
    logging.testcases("TestCase: Remove/Add LIG from/to Enclosure Group")
    logging.testcases("################################################")

    testcase = 'Remove/Add LIG from/to Enclosure Group'
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()
    countdown(0, 5)

    logging.info("Getting Enclosure Group ")
    enc_inst = Enclosures()
    enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
    enc_grp_list = printDict(enc_grp_dict, ['name', 'uri', 'eTag'])
    enc_grp_uri = enc_grp_list[0]['uri']
    enc_grp_etag = enc_grp_list[0]['eTag']

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
    le_dict = LogicalEnclosure()
    le_list = le_dict.GetLogicalEnclosure(ip, auth, api)
    le_uri_list = printDict(le_list, ['uri'])
    LeUri = le_uri_list[0]['uri']

    logging.info("Updating LE from group")
    update_le = UpdateLogicalEnclosure()
    update_le.LeUpdateFromGroup(ip, auth, api, LeUri)

    logging.info("Pausing for 2mins to wait for the LE to updated from group")
    countdown(2, 0)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    logging.info("*******************RESETTING EG TO DEFAULT VALUES ***************************")

    logging.info("Getting list of LIGs")
    ligs_inst = LogicalInterconnectGroup()
    lig_list = ligs_inst.GetListOfLIGs(ip, auth, api)
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
    update_le.LeUpdateFromGroup(ip, auth, api, LeUri)

    logging.info("********************UPDATE FROM GROUP THE LE***************************")

    logging.info("Pausing for 10mins for LE to be updated from group")
    countdown(5, 0)

    logging.info("Checking status of LE")
    GetStatusOfLogicalEnclosure(ip, auth, api)

    logging.info("Pausing 5 mins to power on servers and boot into OS")
    power_cycle_server_inst.power_on_servers(ip, auth, api)
    countdown(5, 0)

    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
    logging.info("Getting the number of FLOGIs")
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)


def testcase_disable_enable_trunking_lig(auth, tor_ip):
    logging.testcases("#########################################")
    logging.testcases("TestCase: Disable/Enable Trunking on LIG")
    logging.testcases("#########################################")

    testcase = 'Disable/Enable Trunking on LIG'

    trunk_inst = ConfigureTOR()
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()
    retrieve_net_inst = Networks()
    power_cycle_server_inst = PowerOffOnServers()
    update_lig_inst = UpdateLogicalInterconnectGroup()
    countdown(0, 2)

    logging.info("Powering down servers before disable trunking on the TOR")
    power_cycle_server_inst.power_off_servers(ip, auth, api)
    countdown(0, 30)

    logging.info("Disable trunking on TOR switch")
    trunk_inst.DisableTrunkingOnE21TORPort4_7(tor_ip, tor_un, tor_pw)
    trunk_inst.DisableTrunkingOnE21TORPort8_11(tor_ip, tor_un, tor_pw)
    trunk_inst.DisableTrunkingOnE21TORPort16_19(tor_ip, tor_un, tor_pw)
    countdown(1, 0)

    logging.info("Getting interconnect types uri")
    interconnect_types_inst = Interconnects()
    ic_types = interconnect_types_inst.GetInterconnectTypes(ip, auth, api)
    ic_type_name = printDict(ic_types, ['uri', 'name'])

    logging.info("Getting list of LIGs")
    ligs_inst = LogicalInterconnectGroup()
    list_of_ligs = ligs_inst.GetListOfLIGs(ip, auth, api)
    li_uri_name = printDict(list_of_ligs, ['uri', 'name'])

    for i, value in enumerate(li_uri_name):
        lig_name = li_uri_name[i]['name']
        if lig_name == "LIG":
            lig_uri = li_uri_name[i]['uri']

    logging.info("Getting Fc network URIs")
    fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle21(
        ip, auth, api)

    fc_mode = 'NONE'
    for s, value in enumerate(ic_type_name):
        ic_type_uri = ic_type_name[s]['uri']
        icm_name = ic_type_name[s]['name']
        if icm_name == "Virtual Connect SE 16Gb FC Module for Synergy":
            update_lig_inst.UpdateLigNoTrunkE21(ip, auth, api, ic_type_uri, lig_uri, fc_net_enc1_bay1_uri,
                                                fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, fc_mode, consistency_check)

    countdown(0, 15)

    logging.info("Getting Logical Interconnects")
    logical_ic_inst = LogicalInterconnects()
    li_ic_list = logical_ic_inst.GetLogicalInterconnects(ip, auth, api)
    li_uri_name = printDict(li_ic_list, ['uri', 'name'])

    logging.info("Updating LI from group, Step 1")
    for i, value in enumerate(li_uri_name):
        logging.info("Updating {} from LIG".format(li_uri_name[i]['name']))
        li_uri = li_uri_name[i]['uri']
        update_li_inst = UpdateLogicalInterconnects()
        update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

    countdown(5, 0)

    fc_mode = 'TRUNK'
    for s, value in enumerate(ic_type_name):
        ic_type_uri = ic_type_name[s]['uri']
        icm_name = ic_type_name[s]['name']
        if icm_name == "Virtual Connect SE 16Gb FC Module for Synergy":
            update_lig_inst.UpdateLigTrunkE21(ip, auth, api, ic_type_uri, lig_uri, fc_net_enc1_bay1_uri,
                                              fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, fc_mode, consistency_check)

    countdown(0, 15)

    logging.info("Getting Logical Interconnects")
    logical_ic_inst = LogicalInterconnects()
    li_ic_list = logical_ic_inst.GetLogicalInterconnects(ip, auth, api)
    li_uri_name = printDict(li_ic_list, ['uri', 'name'])

    logging.info("Updating LI from group step 2")
    for i, value in enumerate(li_uri_name):
        logging.info("Updating {} from LIG".format(li_uri_name[i]['name']))
        li_uri = li_uri_name[i]['uri']
        update_li_inst = UpdateLogicalInterconnects()
        update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

    countdown(5, 0)

    logging.info("Enable trunking on TOR switch")
    trunk_inst.EnableTrunkingOnE21TORPort4_7(tor_ip, tor_un, tor_pw)
    trunk_inst.EnableTrunkingOnE21TORPort8_11(tor_ip, tor_un, tor_pw)
    trunk_inst.EnableTrunkingOnE21TORPort16_19(tor_ip, tor_un, tor_pw)
    countdown(1, 0)

    logging.info("Powering on servers")
    power_cycle_server_inst.power_on_servers(ip, auth, api)
    countdown(7, 0)

    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
    logging.info("Getting the number of FLOGIs")
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

    for s, value in enumerate(ic_type_name):
        ic_type_uri = ic_type_name[s]['uri']
        icm_name = ic_type_name[s]['name']
        if icm_name == "Virtual Connect SE 16Gb FC Module for Synergy":
            update_lig_inst.UpdateLigTrunkVariousSpeedsE21(ip, auth, api, ic_type_uri, lig_uri, fc_net_enc1_bay1_uri,
                                                           fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, fc_mode,
                                                           consistency_check)

    countdown(0, 15)

    logging.info("Powering down servers before running UFG with various port speeds")
    power_cycle_server_inst.power_off_servers(ip, auth, api)
    countdown(0, 30)

    logging.info("Getting Logical Interconnects")
    logical_ic_inst = LogicalInterconnects()
    li_ic_list = logical_ic_inst.GetLogicalInterconnects(ip, auth, api)
    li_uri_name = printDict(li_ic_list, ['uri', 'name'])

    logging.info("Updating LI from group step 3")
    for i, value in enumerate(li_uri_name):
        logging.info("Updating {} from LIG".format(li_uri_name[i]['name']))
        li_uri = li_uri_name[i]['uri']
        update_li_inst = UpdateLogicalInterconnects()
        update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

    countdown(5, 0)

    logging.info("Powering on servers")
    power_cycle_server_inst.power_on_servers(ip, auth, api)
    countdown(7, 0)

    testcase = "Speed set to 4Gb/8Gb/16Gb with trunking Enabled"
    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
    logging.info("Getting the number of FLOGIs")
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)

    fc_mode = 'TRUNK'
    for s, value in enumerate(ic_type_name):
        ic_type_uri = ic_type_name[s]['uri']
        icm_name = ic_type_name[s]['name']
        if icm_name == "Virtual Connect SE 16Gb FC Module for Synergy":
            update_lig_inst.UpdateLigTrunkE21(ip, auth, api, ic_type_uri, lig_uri, fc_net_enc1_bay1_uri,
                                              fc_net_enc1_bay1_quri, fc_net_enc1_bay4_uri, fc_mode, consistency_check)

    countdown(0, 15)
    logging.info("Getting Logical Interconnects")
    logical_ic_inst = LogicalInterconnects()
    li_ic_list = logical_ic_inst.GetLogicalInterconnects(ip, auth, api)
    li_uri_name = printDict(li_ic_list, ['uri', 'name'])

    logging.info("Powering down servers before running UFG to set LIG/LI to default settings")
    power_cycle_server_inst.power_off_servers(ip, auth, api)
    countdown(0, 30)

    logging.info("Updating LI from group step 3")
    for i, value in enumerate(li_uri_name):
        logging.info("Updating {} from LIG".format(li_uri_name[i]['name']))
        li_uri = li_uri_name[i]['uri']
        update_li_inst = UpdateLogicalInterconnects()
        update_li_inst.UpdateLiFromGroup(ip, auth, api, li_uri)

    countdown(5, 0)

    logging.info("Powering on servers")
    power_cycle_server_inst.power_on_servers(ip, auth, api)
    countdown(7, 0)

    all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
    logging.info("Getting the number of FLOGIs")
    get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)


def testcase_update_sp_speeds(auth, eagle, tor_ip):
    logging.testcases("#######################################################")
    logging.testcases("TestCase: Server Profile FC Connection set to 16GB/Auto")
    logging.testcases("#######################################################")

    testcase = 'Server Profile FC Connection set to 16GB/Auto'
    counter = 0
    logging.info("Checking the status of the uplinks ports")
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    server_profile_speeds_inst = ServerProfileConnectionSpeeds()
    update_sp_inst = UpdateServerProfileBfsLunsNewDTO()
    all_states_inst = CheckAllStatesOfCarbon()
    power_cycle_server_inst = PowerOffOnServers()
    retrieve_net_inst = Networks()
    get_num_flogi_inst = GetFLOGI()
    countdown(0, 5)

    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        logging.info("Getting Fc network URIs")
        fc_net_enc1_bay1_uri, fc_net_enc1_bay4_uri, fc_net_enc1_bay1_quri = retrieve_net_inst.get_fc_network_uri_eagle21(
            ip, auth, api)

        power_cycle_server_inst.power_off_servers(ip, auth, api)
        countdown(0, 30)

        logging.info("Getting Enclosure Group ")
        enc_inst = Enclosures()
        enc_grp_dict = enc_inst.EncGroup(ip, auth, api)
        enc_grp_name_uri_list = printDict(enc_grp_dict, ['uri'])
        enc_grp_uri = enc_grp_name_uri_list[0]['uri']

        logging.info("Getting Server HW and Profiles")
        server_hw_profile_inst = Servers()
        array_wwpn1, array_wwpn2, wwnn1_start, wwpn1_start, wwnn2_start, wwpn2_start = server_hw_profile_inst.server_wwnn_start_wwpn_start(
            eagle)
        sp_name, sp_descr, id_1, id_2 = server_hw_profile_inst.server_profile_config()
        sp_dict = server_hw_profile_inst.ServerProfiles(ip, auth, api)
        sp_list = printDict(sp_dict,
                            ['name', 'uri', 'state', 'serverHardwareUri', 'enclosureBay', 'eTag', 'connectionSettings'])
        sp_dict_sorted = sorted(sp_list)

        requested_bw = '16000'
        mode = "UEFI"

        for i, value in enumerate(sp_dict_sorted):
            server_hw_uri = sp_dict_sorted[i]['serverHardwareUri']
            sp_connection_settings = sp_dict_sorted[i]['connectionSettings']
            sp_uri = sp_dict_sorted[i]['uri']
            etag = sp_dict_sorted[i]['eTag']
            sp_name = sp_dict_sorted[i]['name']
            conn_set = sp_connection_settings['connections']
            countdown(0, 15)
            for x, value in enumerate(conn_set):
                if x == 0:
                    wwnn1 = conn_set[x]['wwnn']
                    wwpn1 = conn_set[x]['wwpn']
                elif x == 1:
                    wwnn2 = conn_set[x]['wwnn']
                    wwpn2 = conn_set[x]['wwpn']

            if sp_name == "Server Profile 1" or sp_name == "Server Profile 3" or sp_name == "Server Profile 4":
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

        logging.info("Pausing 7m30s for server profiles to be updated before powering on the servers")
        countdown(7, 30)
        logging.info("*******************POWERING ON SERVERS **********************************")

        tc = "Update Server Profiles to 16Gb"

        logging.info("Checking status of server profiles")
        SPstatus = GetSPStatus(ip, auth, api)
        if SPstatus == "Normal":
            result = "Pass"
        else:
            result = "Fail"

        PassOrFail(result, tc)
        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(7, 0)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        logging.info("Checking FC Connections are set to 16GB speed in Server Profiles")
        server_profile_speeds_inst.ServerProfileConnectionSpeed16GB(ip, auth, api)

        power_cycle_server_inst.power_off_servers(ip, auth, api)
        countdown(0, 30)
        logging.info("*******************UPDATING SERVER PROFILES***************************")

        logging.info("Getting Server HW and Profiles")
        server_hw_profile_inst = Servers()
        array_wwpn1, array_wwpn2, wwnn1_start, wwpn1_start, wwnn2_start, wwpn2_start = server_hw_profile_inst.server_wwnn_start_wwpn_start(
            eagle)
        sp_name, sp_descr, id_1, id_2 = server_hw_profile_inst.server_profile_config()
        sp_dict = server_hw_profile_inst.ServerProfiles(ip, auth, api)
        sp_list = printDict(sp_dict,
                            ['name', 'uri', 'state', 'serverHardwareUri', 'enclosureBay', 'eTag', 'connectionSettings'])
        sp_dict_sorted = sorted(sp_list)
        requested_bw = 'Auto'

        for i, value in enumerate(sp_dict_sorted):
            server_hw_uri = sp_dict_sorted[i]['serverHardwareUri']
            sp_connection_settings = sp_dict_sorted[i]['connectionSettings']
            sp_uri = sp_dict_sorted[i]['uri']
            etag = sp_dict_sorted[i]['eTag']
            sp_name = sp_dict_sorted[i]['name']
            conn_set = sp_connection_settings['connections']
            countdown(0, 15)
            for x, value in enumerate(conn_set):
                if x == 0:
                    wwnn1 = conn_set[x]['wwnn']
                    wwpn1 = conn_set[x]['wwpn']
                elif x == 1:
                    wwnn2 = conn_set[x]['wwnn']
                    wwpn2 = conn_set[x]['wwpn']

            if sp_name == "Server Profile 1" or sp_name == "Server Profile 3" or sp_name == "Server Profile 4":
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

        logging.info("Pausing 7m30s for server profiles to be updated before powering on the servers")
        countdown(7, 30)

        logging.info("*******************POWERING ON SERVERS **********************************")

        tc = "Update Server Profiles to Auto"
        logging.info("Checking status of server profiles")
        SPstatus = GetSPStatus(ip, auth, api)
        if SPstatus == "Normal":
            result = "Pass"
        else:
            result = "Fail"

        PassOrFail(result, tc)
        power_cycle_server_inst.power_on_servers(ip, auth, api)
        countdown(7, 0)

        logging.info("Checking FC Connections are set to Auto speed in Server Profiles")
        server_profile_speeds_inst.ServerProfileConnectionSpeedAuto(ip, auth, api)
        all_states_inst.GetAllStatusOfBothCarbons(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        counter += 1
        countdown(1, 0)
        logging.info("Starting next iteration")


def testcase_reset_carbon(auth, tor_ip):
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
    ul_ports_before = GetCarbonUpLinkPorts(ip, api, auth)
    dl_ports_before = GetCarbonDownLinkPorts(ip, api, auth)
    all_states_inst = CheckAllStatesOfCarbon()
    get_num_flogi_inst = GetFLOGI()

    logging.info("Getting Interconnects")
    ic_inst = Interconnects()
    get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
    ic_name_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName'])

    countdown(0, 5)

    # While loop to reset carbon ICMs
    while counter <= number:
        logging.testcases("iteration: {}".format(counter))
        # For loop to interate thru carbon bay4 and perform reset operation
        logging.info("Resetting the carbon ICMs in bay4")
        for ic, value in enumerate(ic_name_uri_list):
            icm_uri = ic_name_uri_list[ic]['uri']
            icm_name = ic_name_uri_list[ic]['name']
            enc_name = ic_name_uri_list[ic]['enclosureName']
            carbon_reset = PowerStateOfCarbon()
            if icm_name == "{}, interconnect 4".format(enc_name):
                logging.info("Performing Reset operation on the carbon in {}".format(icm_name))
                carbon_reset.ResetCarbon(ip, auth, api, icm_uri)
            else:
                pass

        countdown(7, 0)
        logging.info("Checking to see the state of the carbon in bay4")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay4(ip, auth, api, ul_ports_before, dl_ports_before, testcase)

        # For loop to iterate thru carbon bay1 and power it off
        logging.info("Resetting the carbon ICMs in bay1")
        for ic, value in enumerate(ic_name_uri_list):
            icm_uri = ic_name_uri_list[ic]['uri']
            icm_name = ic_name_uri_list[ic]['name']
            enc_name = ic_name_uri_list[ic]['enclosureName']
            if icm_name == "{}, interconnect 1".format(enc_name):
                logging.info("Performing Reset operation on the carbon in {}".format(icm_name))
                carbon_reset.ResetCarbon(ip, auth, api, icm_uri)
            else:
                pass

        countdown(7, 0)
        logging.info("Checking to see the state of the carbon in bay4")
        get_num_flogi_inst.get_flogi_enclosure(ip, tor_ip, tor_un, tor_pw)
        all_states_inst.GetAllStatusOfCarbonsBay1(ip, auth, api, ul_ports_before, dl_ports_before, testcase)
        counter += 1
        countdown(0, 30)
        logging.info("Starting next iteration")


def main():
    tor_ip = get_tor_ip(ip)
    eagle = get_eagle_enclosure_map(ip)
    setup_logging_Enhanced(eagle, filename)
    check_cim_ready()
    auth = get_AT()
    get_enc_name_list = Enclosures()
    enc_name = get_enc_name_list.get_enclosure_name(ip, auth, api)
    get_ov_build_carbon_fw_version(auth, enc_name)
    #THIS SECTION OF CODE CONFIGURES EAGLE21
    create_fc_networks(auth)
    enc_uri = get_enclosure_uri(auth)
    ic_types_uri, ic_types_name = interconnect_type_uri(auth)
    create_lig(auth, ic_types_uri, ic_types_name)
    lig_uri = get_lig_uri(auth)
    create_enclosure_group(auth, lig_uri)
    enc_grp_uri = get_eg_uri(auth)
    create_le(auth, enc_uri, enc_grp_uri)
    check_le_status(auth)
    create_server_profiles(auth, eagle, enc_grp_uri)
    check_sp_status(auth)
    preflight_check(auth, tor_ip)
    #THIS SECTION OF CODE STARTS THE REGRESSION TESTCASES
    testcase_power_off_on_carbon(auth, tor_ip)
    testcase_efuse_carbon(auth, tor_ip)
    testcase_efuse_carbon_power_off(auth, tor_ip)
    testcase_reset_carbon(auth, tor_ip)
    testcase_restart_oneview(auth, tor_ip)
    testcase_icm_utilization(auth)
    testcase_remote_syslog(auth)
    testcase_connectorinfo_digitaldiag(auth)
    testcase_staticIp_add_remove_encgrp(auth, tor_ip)
    testcase_remove_add_fc_network_lig(auth, tor_ip)
    testcase_remove_add_fc_network_li(auth, tor_ip)
    testcase_aside_bside_ligs(auth, tor_ip)
    testcase_portspeed_4_8_16_tor(auth, tor_ip)
    testcase_port_mirror(auth, tor_ip)
    testcase_remove_add_lig_encgrp(auth, tor_ip)
    testcase_disable_enable_trunking_lig(auth, tor_ip)
    testcase_update_sp_speeds(auth, eagle, tor_ip)


if __name__ == '__main__':
    main()
