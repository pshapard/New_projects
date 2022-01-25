#/usr/bin/python
#Author: Patrick Shapard @HPE, 
#created: 1/05/2022
#updated: 1/05/2022
#This script is used to automate the deletion of a configuration on a Synergy single or multi-enclosure.


import logging
import sys

from requests.exceptions import ConnectionError

from SynergyV3800 import DeleteEnclosureGroup
from SynergyV3800 import DeleteLogicalEnclosure
from SynergyV3800 import DeleteLogicalInterconnectGroup
from SynergyV3800 import DeleteNetworks
from SynergyV3800 import DeleteServerProfiles
from SynergyV3800 import Enclosures
from SynergyV3800 import GetSPStatus
from SynergyV3800 import GetStatusOfLogicalEnclosure  # function
from SynergyV3800 import Interconnects
from SynergyV3800 import IsResourceDeleted
from SynergyV3800 import LogicalEnclosure
from SynergyV3800 import LogicalInterconnectGroup
from SynergyV3800 import LoginCreds
from SynergyV3800 import Networks
from SynergyV3800 import OneViewBuildVersion
from SynergyV3800 import PassOrFail  # function
from SynergyV3800 import PowerOffOnServers
from SynergyV3800 import Servers
from SynergyV3800 import api, username, ov_pw
from SynergyV3800 import countdown  # function
from SynergyV3800 import get_eagle_enclosure_map
from SynergyV3800 import printDict  # function
from SynergyV3800 import setup_logging_Enhanced
from SynergyV3800 import get_filename



filename = "DeleteUmbrellaSynergyV3800"


def get_auth_token(ip):
    login_inst = LoginCreds()
    try:
        auth = login_inst.LoginToken(ip, api, username, ov_pw)
    except ConnectionError as e:
        logging.info("Could not connect to host")
        logging.info("{}" .format(e))
        sys.exit(0)
    return auth


def get_ip_from_command_line():
    if len(sys.argv) < 2:
        print("ERROR: Please provide the ip address of the enclosure  \n")
        print('Usage: %s [ip address of enclosure] ' % sys.argv[0])
        print("example: %s 15.186.9.21 " % sys.argv[0])
        sys.exit(1)

    return sys.argv[1]


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
    logging.testcases("##############################")
    logging.testcases("TestCase: Delete Configuration")
    logging.testcases("##############################")


def delete_server_profiles(ip, auth):
    TC = "Delete Server Profiles"
    Resource = IsResourceDeleted()
    status = Resource.IsSPDeleted(ip, auth, api)
    if status is True:
        logging.info("Server Profiles have been Deleted")
    elif status is False:
        logging.info("Getting Server Profiles")
        ServerHwProfiles = Servers()
        ServerProfileList = ServerHwProfiles.ServerProfiles(ip, auth, api)
        ServerProfileUri = printDict(ServerProfileList, ['uri'])
        ServerProfileNames = printDict(ServerProfileList, ['name'])
        power_cycle_server = PowerOffOnServers()
        power_cycle_server.power_off_servers(ip, auth, api)
        
        for i in range(0, len(ServerProfileUri)):
            SpUri = ServerProfileUri[i]['uri']
            name = ServerProfileNames[i]['name']
            logging.info("Deleting Server Profile {}" .format(name))
            countdown(20)
            RemoveServerProfile = DeleteServerProfiles()
            RemoveServerProfile.DeleteSP(ip, auth, api, SpUri)
    
        logging.info("Deleting {} server profile(s)" .format(len(ServerProfileUri)))
        logging.info("pausing 3m30s for the server profiles to be deleted")
        countdown(210)
        logging.info("Checking to see if server profiles have been deleted")
        status = Resource.IsSPDeleted(ip, auth, api)
        if status == True:
            logging.info("Server Profiles have been Deleted")
            result = "Pass"
        elif status == False:
            logging.error("Server Profiles have not been deleted")
            logging.info("Waiting 2 minutes to check status of server profiles")
            countdown(120)
            count = 0
            while status == False:
                status = Resource.IsSPDeleted(ip, auth, api)
                if status == True:
                    logging.info("Server Profiles have been Deleted")
                    result = "Pass"
                    break
                elif status == False:
                    logging.error("Server Profiles still not deleted, will check again in a minute")
                    countdown(60)
                    if count == 10:
                        logging.error("Server Profile(s) could not be deleted. Quiting script")
                        result = "Fail"
                        PassOrFail(result,TC)
                        sys.exit(0)
                count =+ 1
    
        PassOrFail(result,TC)


def delete_server_profile_templates(ip, auth):
    TC = "Delete Server Profiles"
    Resource = IsResourceDeleted()
    status = Resource.IsSPTDeleted(ip, auth, api)
    if status is True:
        logging.info("Server Profile Templates have been Deleted")
    elif status is False:
        logging.info("Getting Server Profile Templates")
        ServerHwProfiles = Servers()
        ServerProfileTemplateList = ServerHwProfiles.ServerProfilesTemplates(ip, auth, api)
        ServerProfileTemplateUri = printDict(ServerProfileTemplateList, ['uri'])
        ServerProfileTemplateNames = printDict(ServerProfileTemplateList, ['name'])
        power_cycle_server = PowerOffOnServers()
        power_cycle_server.power_off_servers(ip, auth, api)
        
        for i in range(0, len(ServerProfileTemplateUri)):
            spt_uri = ServerProfileTemplateUri[i]['uri']
            spt_name = ServerProfileTemplateNames[i]['name']
            logging.info("Deleting Server Profile template {}" .format(spt_name))
            countdown(5)
            RemoveServerProfileTemplate = DeleteServerProfiles()
            RemoveServerProfileTemplate.delete_sp_template(ip, auth, api, spt_uri)
    
        logging.info("Deleting {} server profile(s)" .format(len(ServerProfileTemplateUri)))
        logging.info("pausing 3m30s for the server profile templates to be deleted")
        logging.info("Checking to see if server profile templates have been deleted")
        status = Resource.IsSPTDeleted(ip, auth, api)
        if status is True:
            logging.info("Server Profile Templates have been Deleted")
            result = "Pass"
        elif status is False:
            logging.error("Server Profile Templates have not been deleted")
            GetSPStatus(ip,auth,api)
            if status is True:
                logging.info("Server Profile Templates have been Deleted")
                result = "Pass"
            elif status is False:
                logging.error("Server Profile Template(s) could not be deleted. Quiting script")
                result = "Fail"
                PassOrFail(result,TC)
                sys.exit(0)
    
        PassOrFail(result,TC)



def delete_logical_enclosure(ip, auth):
    Resource = IsResourceDeleted()
    LeState = Resource.IsLeDeleted(ip, auth, api)
    if LeState is True:
        logging.info("The Logical Enclosure has been deleted or not present")
    elif LeState is False:
        logging.info("Getting Logical Enclosure")
        LeList = LogicalEnclosure()
        LeDict = LeList.GetLogicalEnclosure(ip, auth, api)
        LeUriList = printDict(LeDict, ['uri'])
        LeUri = LeUriList[0]['uri']
        TC = "Delete Logical Enclosure"
        logging.info("Deleting Logical Enclosure")
        RemoveLe = DeleteLogicalEnclosure()
        RemoveLe.DeleteLE(ip, auth, api, LeUri)
        
        logging.info("Pausing 6 mins to delete the LE.")
        countdown(360)
    
        logging.info("Checking to see if LE has been deleted")
        LeState = Resource.IsLeDeleted(ip, auth, api)
        if LeState is True:
            logging.info("LE is Deleted")
            result = "Pass"
        elif LeState is False:
            logging.info("LE has not been deleted")
            logging.info("Checking the status of the LE")
            GetStatusOfLogicalEnclosure(ip, auth, api)
            result = "Fail"
    
        PassOrFail(result,TC)


def delete_enclosure_group(ip, auth):
    TC = "Delete Enclosure Group"
    Resource = IsResourceDeleted()
    EgState = Resource.IsEgDeleted(ip, auth, api)
    if EgState is True:
        logging.info("The Enclosure Group has been deleted or is not present")
    elif EgState is False:
        logging.info("Getting Enclosure Group ")
        EnclosureGroup = Enclosures()
        EncGroupList = EnclosureGroup.EncGroup(ip, auth, api)
        EncGrpUri = printDict(EncGroupList, ['uri'])
        for i in range(0, len(EncGrpUri)):
            GroupUri = EncGrpUri[i]['uri']
            logging.info("Deleting Enclosure Group")
            RemoveEG = DeleteEnclosureGroup()
            RemoveEG.DeleteEG(ip, auth, api, GroupUri)
        
        logging.info("pausing 15 secs to delete EG")
        countdown(15)
        
        EgState = Resource.IsEgDeleted(ip, auth, api)
        if EgState is True:
            logging.info("Enclosure Group is deleted")
            result = "Pass"
        elif EgState is False:
            logging.info("Enclosure Group has not been deleted")
            result = "Fail"
    
        PassOrFail(result,TC)


def delete_logical_enclosure_group(ip, auth):
    TC = "Delete Logical Interconnect Group"
    Resource = IsResourceDeleted()
    LigState = Resource.IsLIGDeleted(ip, auth, api)
    if LigState is True:
        logging.info("The LIG(s) has/have been deleted or is not present")
    elif LigState is False:
        logging.info("Getting List of LIGs")
        Lig = LogicalInterconnectGroup()
        LigList = Lig.GetListOfLIGs(ip, auth, api)
        LigUri = printDict(LigList, ['uri'])
        for i in range(0, len(LigUri)):
            uri = LigUri[i]['uri']
            RemoveLig = DeleteLogicalInterconnectGroup()
            RemoveLig.DeleteLIG(ip, auth, api, uri)
        logging.info("Deleting LIGs")
        logging.info("pausing 15 secs to delete LIG")
        countdown(15)
    
        LigStatus = Resource.IsLIGDeleted(ip, auth, api)
        if LigStatus is True:
            logging.info("Logical Interconnect Group is deleted")
            result = "Pass"
        elif LigStatus is False:
            logging.info("Logical Interconnect Group has not been deleted")
            result = "Fail"
    
        PassOrFail(result,TC)


def delete_fc_networks(ip, auth):
    TC = "Delete Fibre Channel Networks"
    Resource = IsResourceDeleted()
    RetrieveNetworks = Networks()
    FcNetworkState = Resource.IsFcNetDeleted(ip, auth, api)
    if FcNetworkState is True:
        logging.info("The FC network(s) has/have been deleted or is/are not present")
        result = "Pass"
    elif FcNetworkState is False:
        logging.info("getting FC Networks")
        FcNetworksList = RetrieveNetworks.GetFcNetworks(ip, auth, api)
        FcNetList = printDict(FcNetworksList, ['name', 'uri'])
        for i in range(0,len(FcNetList)):
            name = FcNetList[i]['name']
            uri = FcNetList[i]['uri']
            logging.info ("Deleting %s FC network" %name)
            RemoveFcNet = DeleteNetworks()
            RemoveFcNet.DeleteFcNetwork(ip, auth, api, uri)
        countdown(7)
        FcNetworkState = Resource.IsFcNetDeleted(ip, auth, api)
        if FcNetworkState is True:
            logging.info("Fibre Channel networks have been deleted")
            result = "Pass"
        elif FcNetworkState is False:
            logging.info("Fibre Channel networks have not been deleted")
            result = "Fail"
        
    PassOrFail(result,TC)    


def delete_ethernet_networks(ip, auth):
    TC = "Delete Ethernet networks"
    RetrieveNetworks = Networks()
    Resource = IsResourceDeleted()
    EthernetNetworkState = Resource.IsEthernetDeleted(ip, auth, api)
    if EthernetNetworkState is True:
        logging.info("The ethernet network(s) has/have been deleted or is/are not present")
        result = "Pass"
    elif EthernetNetworkState is False:
        logging.info("getting Ethernet Networks")
        EthernetNetList = RetrieveNetworks.GetEthernetNetworks(ip, auth, api)
        EthNetList = printDict(EthernetNetList, ['name', 'uri'])
        for i in range(0,len(EthNetList)):
            name = EthNetList[i]['name']
            uri = EthNetList[i]['uri']
            logging.info("Deleting {} Ethernet network" .format(name))
            RemoveFcNet = DeleteNetworks()
            RemoveFcNet.DeleteFcNetwork(ip, auth, api, uri)
    
        EthernetNetworkState = Resource.IsEthernetDeleted(ip, auth, api)
        if EthernetNetworkState is True:
            logging.info("Ethernet networks have been deleted")
            result = "Pass"
        elif EthernetNetworkState is False:
            logging.info("Ethernet networks have not been deleted")
            result = "Fail"
        
    PassOrFail(result,TC)


def delete_fcoe_networks(ip, auth):
    TC = "Delete Ethernet networks"
    RetrieveNetworks = Networks()
    Resource = IsResourceDeleted()
    FCoENetworkState = Resource.IsFCoEDeleted(ip, auth, api)
    if FCoENetworkState is True:
        logging.info("The FCoE network(s) has/have been deleted or is/are not present")
        result = "Pass"
    elif FCoENetworkState is False:
        logging.info("getting FCoE Networks")
        FCoENetList = RetrieveNetworks.GetFCoENetworks(ip, auth, api)
        EthNetList = printDict(FCoENetList, ['name', 'uri'])
        for i in range(0,len(EthNetList)):
            name = EthNetList[i]['name']
            uri = EthNetList[i]['uri']
            logging.info("Deleting {} FCoE network" .format(name))
            RemoveFcNet = DeleteNetworks()
            RemoveFcNet.DeleteFcNetwork(ip, auth, api, uri)
    
        FCoENetworkState = Resource.IsFCoEDeleted(ip, auth, api)
        if FCoENetworkState is True:
            logging.info("FCoE networks have been deleted")
            result = "Pass"
        elif FCoENetworkState is False:
            logging.info("FCoE networks have not been deleted")
            result = "Fail"
        
    PassOrFail(result,TC)



    
def main():
    ip = get_ip_from_command_line()
    eagle = get_eagle_enclosure_map(ip)
    #filename = get_filename()
    setup_logging_Enhanced(filename, eagle)
    auth = get_auth_token(ip)
    get_enc_name_list = Enclosures()
    enc_name = get_enc_name_list.get_enclosure_name(ip, auth, api)
    get_ov_build_icm_fw_version(ip, auth, enc_name)
    delete_server_profiles(ip, auth)
    delete_server_profile_templates(ip, auth)
    delete_logical_enclosure(ip, auth)
    delete_enclosure_group(ip, auth)
    delete_logical_enclosure_group(ip, auth)
    delete_fc_networks(ip, auth)
    delete_ethernet_networks(ip, auth)
    delete_fcoe_networks(ip, auth)


if __name__ == '__main__':
    main()


logging.info("End of script")