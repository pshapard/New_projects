#/usr/bin/python
#Author: Patrick Shapard
#created: 05/08/2018
#updated: 05/08/2018
#This script automates the inventory process of carbon dev team/FVt-CRM enclosures
#It takes inventory of Interconnects and servers.  More is comming.

import sys
import logging
import socket
from SynergyV1400 import sshclient
from SynergyV1400 import LoginCreds
from SynergyV1400 import OneViewBuildVersion
from SynergyV1400 import Interconnects
from SynergyV1400 import get_eagle_enclosure_map
from SynergyV1400 import setup_logging_Enhanced
from SynergyV1400 import Servers
from SynergyV1400 import Enclosures
from SynergyV1400 import GetSPStatus
from SynergyV1400 import printDict  # function
from SynergyV1400 import countdown  # function
from requests.exceptions import ConnectionError

filename = 'SE_EncInventorySynergyV1400'

#While loop to check if the CIM is ready to receive login requests
def get_ip_from_command_line():
    if len(sys.argv) < 2:
        print "ERROR: Please provide the ip address of the enclosure  \n"
        print 'Usage: %s [ip address of enclosure] ' % sys.argv[0]
        print "example: %s 15.186.9.21 " % sys.argv[0]
        sys.exit(1)

    ip = sys.argv[1]
    return ip

def check_cim_ready(ip):
    # While loop to check if the CIM is ready to receive login requests
    count = 0
    while True:
        cmd = 'ls -l'
        try:
            sshclient(ip, user, cim_pw, cmd)
            logging.info("The CIM is ready for login requests, moving on")
            break
        except socket.error as e:
            logging.info("The CIM is not ready for login requests")
        count = count + 1
        if count == 20:
            logging.info("Unable to connect to the CIM, quitting script")
            sys.exit(0)
        else:
            pass
        countdown(1, 0)


def retrieve_my_creds(ip):
    login_inst = LoginCreds()
    try:
        login_inst.InitialLogin(ip, api)
        auth = login_inst.LoginToken(ip, api, username, password)
        return auth
    except ConnectionError as e:
        logging.info("Could not connect to host")
        #logging.info("{}" .format(e))
        sys.exit(0)

def get_ov_build_icm_fw_version(ip, auth, enc_name):
    get_build_inst = OneViewBuildVersion()
    ic_fw_inst = Interconnects()
    carbon_fw_version = ic_fw_inst.getCarbonFwVersion(ip, auth, api, enc_name)
    potash_fw_version = ic_fw_inst.getPotashFwVersion(ip, auth, api, enc_name)
    nitro_fw_version = ic_fw_inst.getNitroFwVersion(ip, auth, api, enc_name)
    version = get_build_inst.GetOVBuild(ip, auth, api)
    logging.testcases("The OneView version/build is: {}".format(version))
    logging.testcases("The ip address of this enclosure is: {}".format(ip))
    logging.testcases("The carbon fw version is: {}".format(carbon_fw_version))
    logging.testcases("The potash fw version is: {}".format(potash_fw_version))
    logging.testcases("The nitro fw version is: {}".format(nitro_fw_version))

def enclosure_inventory(ip, auth):
	logging.info("Getting Enclosures ")
	enc_inst = Enclosures()
	EncDict = enc_inst.GetEnc(ip,auth,api)
	EncNumType = EncDict['count']
	EncNum = str(EncNumType)
	logging.testcases("The number of enclosures is: {}".format(EncNum))
	enc_list = printDict(EncDict, ['name', 'version', 'state'])
	flm_mgr_bays = printDict(EncDict, ['managerBays'])
	cim_mgr_list = printDict(EncDict, ['applianceBays'])
	for i, value in enumerate(enc_list):
		name =  enc_list[i]['name']
		enc_version =  enc_list[i]['version']
		enc_state =  enc_list[i]['state']
		logging.testcases("Name of enclosure: {}".format(name))
		logging.testcases("The enclosure version: {}".format(enc_version))
		logging.testcases("The state of enclosure: {}".format(enc_state))
		flm_bays = flm_mgr_bays[i]['managerBays']
		cim_bays = cim_mgr_list[i]['applianceBays']
		for x, value in enumerate(flm_bays):
			flm_bay_num = flm_bays[x]['bayNumber']
			flm_fw_ver = flm_bays[x]['fwVersion']
			flm_fw_bld_date = flm_bays[x]['fwBuildDate']
			logging.testcases("fw version for FLM in bay {} is {} build date {}".format(flm_bay_num, flm_fw_ver, flm_fw_bld_date))
		for k, value in enumerate(cim_bays):
			cim_sn = cim_bays[k]['serialNumber']
			cim_presence = cim_bays[k]['devicePresence']
			cim_model = cim_bays[k]['model']
			cim_bay_num = cim_bays[k]['bayNumber']
			logging.testcases("CIM SN {} in bay {} is {} ".format(cim_sn, cim_bay_num, cim_presence))

	logging.info("Getting Server HW and Profiles")
	server_hw_profiles_inst = Servers()
	ServerHwList = server_hw_profiles_inst.ServerHW(ip,auth,api)
	ServerProfileList = server_hw_profiles_inst.ServerProfiles(ip,auth,api)
	ServerHwNames = printDict(ServerHwList, ['name'])
	server_hw_dict = printDict(ServerHwList, ['uri','name','model','memoryMb','mpFirmwareVersion','romVersion',
	                                         'mpHostInfo','processorCoreCount','processorCount','processorType','serialNumber', 'partNumber'])
	ServerHwPowerSate = printDict(ServerHwList, ['powerState'])
	ServerProfileNames = printDict(ServerProfileList, ['name'])
	ServerProfileEncUri = printDict(ServerProfileList, ['enclosureUri'])
	ServerProfileEncBay = printDict(ServerProfileList, ['enclosureBay'])
	
	logging.testcases("#"*90)
	SortHWList = sorted(ServerHwNames)
	numofservers = len(SortHWList)
	logging.testcases("The number of servers is: {}".format(numofservers))
	
	for i, value in enumerate(server_hw_dict):
		server_iLO_host_info = server_hw_dict[i]['mpHostInfo']
		name_of_server = server_hw_dict[i]['name']
		server_sn = server_hw_dict[i]['serialNumber']
		server_pn = server_hw_dict[i]['partNumber']
		server_uri = server_hw_dict[i]['uri']
		server_model = server_hw_dict[i]['model']
		server_memory = server_hw_dict[i]['memoryMb']
		server_iLO_version = server_hw_dict[i]['mpFirmwareVersion']
		server_rom_version = server_hw_dict[i]['romVersion']
		server_cpu_core_count = server_hw_dict[i]['processorCoreCount']
		server_cpu_count = server_hw_dict[i]['processorCount']
		server_cpu_type = server_hw_dict[i]['processorType']
		server_iLO_hostname = server_iLO_host_info['mpHostName']
		server_iLO_ip_address_list = server_iLO_host_info['mpIpAddresses']
		logging.testcases("#"*90)
		logging.testcases("Server model: {}".format(server_model))
		logging.testcases("Server SN: {}".format(server_sn))
		logging.testcases("Server PN: {}".format(server_pn))
		logging.testcases("Name of server: {}".format(name_of_server))
		logging.testcases("Server memory: {}".format(server_memory))
		logging.testcases("Server cpu core count: {}".format(server_cpu_core_count))
		logging.testcases("Server cpu count: {}".format(server_cpu_count))
		logging.testcases("Server cpu type: {}".format(server_cpu_type))
		logging.testcases("Server ROM ver: {}".format(server_rom_version))
		logging.testcases("Server iLO ver: {}".format(server_iLO_version))
		logging.testcases("Server iLO hostname: {}".format(server_iLO_hostname))
		for x, value in enumerate(server_iLO_ip_address_list):
			ip_address_type = server_iLO_ip_address_list[x]['type']
			ip_address = server_iLO_ip_address_list[x]['address']
			if ip_address_type == 'LinkLocal':
				logging.testcases("iLO IPv6 linklocal address: {}".format(ip_address))
			elif ip_address_type == 'DHCP':
				logging.testcases("iLO IPv4 dhcp address: {}".format(ip_address))
		server_fw_list = server_hw_profiles_inst.server_hw_firmware_inventory(ip, auth, api, server_uri)
		server_comp = sorted(server_fw_list['components'])
		for e, value in enumerate(server_comp):
			server_comp_name = server_comp[e]['componentName']
			server_comp_ver = server_comp[e]['componentVersion']
			logging.testcases("{}: {}" .format(server_comp_name, server_comp_ver))

	logging.testcases("#"*90 )
	EnclosureModel = printDict(EncDict, ['enclosureModel'])
	EnclosureName = printDict(EncDict, ['name'])
	EnclosureUri = printDict(EncDict, ['uri'])
	EnclosureRefreshState = printDict(EncDict, ['refreshState'])
	EnclosureState = printDict(EncDict, ['state'])
	EnclosureICBays = printDict(EncDict, ['interconnectBays'])
	
	ICModelListDict = []
	ICFwListDict = []
	for i, value in enumerate(EnclosureName):
		name =  EnclosureName[i]['name']
		ic_inst = Interconnects()
		get_ic = ic_inst.GetInterconnectMultiEnc(ip,auth,api,name)
		ic_all_info_dict = printDict(get_ic,['model','name','state','firmwareVersion','ipAddressList','serialNumber', 'partNumber'])
		for j, value in enumerate(ic_all_info_dict):
			ModelList = ic_all_info_dict[j]['model']
			FwVersion = ic_all_info_dict[j]['firmwareVersion']
			ic_name = ic_all_info_dict[j]['name']
			ic_state = ic_all_info_dict[j]['state']
			ic_ip_list = ic_all_info_dict[j]['ipAddressList']
			ic_sn = ic_all_info_dict[j]['serialNumber']
			ic_pn = ic_all_info_dict[j]['partNumber']
			logging.testcases("The interconnect location: {}".format(ic_name))
			logging.testcases("The interconnect model: {}".format(ModelList))
			logging.testcases("The interconnect firmware: {}".format(FwVersion))
			logging.testcases("The interconnect state: {}".format(ic_state))
			logging.testcases("The interconnect SN: {}".format(ic_sn))
			logging.testcases("The interconnect PN: {}".format(ic_pn))
			for x, value in enumerate(ic_ip_list):
				ic_ip_address_type = ic_ip_list[x]['ipAddressType']
				ic_ip_address = ic_ip_list[x]['ipAddress']
				if ic_ip_address_type == 'Ipv6LinkLocal':
					logging.testcases("The interconnect IPv6 linklocal address: {}".format(ic_ip_address))
				elif ic_ip_address_type == 'Ipv4Dhcp':
					logging.testcases("The interconnect IPv4 dhcp address: {}".format(ic_ip_address))
			ICModelListDict.append(ModelList)
			logging.testcases("#"*90)
		NumOfICM = len(ICModelListDict)
	
	logging.info("Getting Server HW and Profiles")
	server_hw_profiles_inst = Servers()
	ServerHwList = server_hw_profiles_inst.ServerHW(ip,auth,api)
	ServerProfileList = server_hw_profiles_inst.ServerProfiles(ip,auth,api)
	ServerHwNames = printDict(ServerHwList, ['name'])
	ServerHwUri = printDict(ServerHwList, ['uri'])
	ServerHwModel = printDict(ServerHwList, ['model'])
	ServerHwPowerSate = printDict(ServerHwList, ['powerState'])
	ServerProfileNames = printDict(ServerProfileList, ['name'])
	ServerProfileEncUri = printDict(ServerProfileList, ['enclosureUri'])
	ServerProfileEncBay = printDict(ServerProfileList, ['enclosureBay'])
	SPNamesSorted = sorted(ServerProfileNames)
	
	NumOfServerProfiles = len(ServerProfileNames)
	
	for i, value in enumerate(SPNamesSorted):
		try:
			Name = SPNamesSorted[i]['name']
			logging.testcases("Server profile name is: {}".format(Name))
		except IndexError:
			logging.testcases("There are no server profiles")
	
	SPstatus = GetSPStatus(ip,auth,api)
	
	logging.info("Getting Enclosures ")
	enc_inst = Enclosures()
	EncDict = enc_inst.GetEnc(ip, auth, api)
	EnclosureModel = printDict(EncDict, ['enclosureModel'])
	EnclosureName = printDict(EncDict, ['name'])
	EnclosureUri = printDict(EncDict, ['uri'])
	EnclosureRefreshState = printDict(EncDict, ['refreshState'])
	EnclosureState = printDict(EncDict, ['state'])
	
	logging.testcases("The number of interconnects: {}".format(NumOfICM))
	logging.testcases("The number of servers: {}".format(numofservers))
	logging.testcases("The number of enclosures:  {}".format(EncNum))
	logging.testcases("The number of server profiles: {}".format(NumOfServerProfiles))

def main():
    ip = get_ip_from_command_line()
    enclosure = get_eagle_enclosure_map(ip)
    setup_logging_Enhanced(enclosure, filename)
    check_cim_ready(ip)
    auth = retrieve_my_creds(ip)
    get_enc_name_list = Enclosures()
    enc_name = get_enc_name_list.get_enclosure_name(ip, auth, api)
    logging.testcases("#"*100)
    get_ov_build_icm_fw_version(ip, auth, enc_name)
    enclosure_inventory(ip, auth)


if __name__ == '__main__':
    main()