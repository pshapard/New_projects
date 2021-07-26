#/usr/bin/python
#Author: Patrick Shapard @HPE,
#created: 05/26/2021
#updated: 06/24/2021
#This module is to be used for Oneview(OV 6.20) release with C7000 hardware.


import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
import sys
import os
import logging
import requests
import json
import paramiko
import time
import subprocess
import tarfile

__author__ = "Patrick Shapard, patrick.shapard@hpe.com"
__version__ = "3000"

api = 3000
username = os.environ['USERNAME']
tor_pw = os.environ['TOR_PW']
user = os.environ['USER']
tor_un = os.environ['TOR_UN']
ov_pw = os.environ['OV_PW']
old_pw = os.environ['OLD_PW']
cim_pw = os.environ['CIM_PW']


class LoginCreds(object):
    
    def loginSessions(self, ip, api, username, ov_pw):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/login-sessions" % ip
        payload = "{\"userName\":\"%s\",\"password\":\"%s\"}" % (username, ov_pw)
        headers = {
            'x-api-version': api,
            'content-type': "application/json"
            }
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
        
    def InitialLogin(self, ip, api, ov_pw, old_pw):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/users/changePassword" %ip
        payload = "{\r\n    \"newPassword\" : \"%s\",\r\n    \"oldPassword\" : \"%s\",\r\n    \"userName\" : \"Administrator\"\r\n}\r\n" %(ov_pw, old_pw)
        headers = {
            'x-api-version': api,
            'content-type': "application/json"
            }
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
        
    def LoginToken(self, ip, api, username, ov_pw):
        #Getting authentication token
        login = LoginCreds()
        Authenticate = login.loginSessions(ip, api, username, ov_pw)
        auth = Authenticate['sessionID']
        return auth
    
    def AcceptEULA(self, ip, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/appliance/eula/save" % ip
        payload = "    {\r\n        \"supportAccess\" : \"yes\"\r\n    }"
        headers = {
            'x-api-version': api,
            'content-type': "application/json"
            }
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))


class OneViewBuildVersion(object):

    def GetOVBuild(self, ip, auth, api):
        ov_inst = OneViewBuildVersion()
        OvBuildList = ov_inst.GetOneView(ip, auth, api)
        OneViewVersion = OvBuildList['softwareVersion']
        return OneViewVersion
    
    def GetOneView(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/appliance/nodeinfo/version" % ip
        headers = {
            'x-api-version': api,
            'auth': auth,
            'content-type': "application/json"
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)    
        return(json.loads(response.text))


class Enclosures(object):

    def ClaimC7KEnc(slef, ip, auth, api, enc_grp_uri, oa_pw, oa_ip):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/enclosures" %ip
        payload = "{\r\n   \"hostname\" : \"%s\",\r\n   \"username\" : \"Administrator\",\r\n   \"password\" : \"%s\",\r\n   \"licensingIntent\" : \"OneView\",\r\n   \"force\" : \"false\",\r\n   \"enclosureGroupUri\" : \"%s\",\r\n   \"forceInstallFirmware\" : false\r\n}" %(oa_ip, oa_pw, enc_grp_uri)
        headers = {
            'auth': auth,
            'x-api-version': api,
            'content-type': "application/json"
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)


    def GetEnc(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/enclosures" % ip
        headers = {
            'x-api-version': api,
            'content-type': "application/json",
            'auth': auth
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
    
    def EncGroup(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/enclosure-groups" % ip
        headers = {
            'x-api-version': api,
            'auth': auth
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
    
    def RestartOneview(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        logging.info("Restarting OneView\n")
        url = "https://%s/rest/appliance/shutdown?type=REBOOT" %ip
        headers = {
            'auth': auth,
            'x-api-version': api,
            }
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
    
    def get_enclosure_name_old(self, ip, auth, api):
        logging.info("Getting Enclosure Group ")
        enc_instance = Enclosures()
        enc_dict = enc_instance.GetEnc(ip, auth, api)
        enc_name_list = printDict(enc_dict, ['name'])
        print enc_name_list
        for x, value in enumerate(enc_name_list):
            each_enc_name = enc_name_list[x]['name']
        return each_enc_name
    
    def get_enclosure_name(self, ip, auth, api):
        EncNameDict = []
        logging.info("Getting Enclosure Group ")
        enc_instance = Enclosures()
        enc_dict = enc_instance.GetEnc(ip, auth, api)
        enc_name_list = printDict(enc_dict, ['name'])
        for x, value in enumerate(enc_name_list):
            each_enc_name_list = enc_name_list[x]['name']
            EncNameDict.append(each_enc_name_list)
        return EncNameDict
    
    def update_enc_name(self, ip, api, auth, id, new_name):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://{}/rest/enclosures/{}" .format(ip, id)
        payload = "[\r\n    { \"op\": \"replace\", \"path\": \"/name\", \"value\": \"%s\" }\r\n]" %new_name
        headers = {
            'auth': auth,
            'x-api-version': api,
            'Content-Type': "application/json",
            'If-Match': "*"
            }
        response = requests.request("PATCH", url, data=payload, headers=headers, verify=False)
        logging.debug(payload)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)


class RemoveEnclosure(object):

    def RemoveEnc(self, ip, auth, api, enc_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s%s" %(ip, enc_uri)
        headers = {
            'auth': auth,
            'x-api-version': api
            }
        logging.debug("url: %s" % url)
        response = requests.request("DELETE", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)


class Networks(object):

    def GetFcNetworks(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/fc-networks?start=0&count=275" % ip
        headers = {
            'x-api-version': api,
            'auth': auth
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
    
    def GetEthernetNetworks(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/ethernet-networks?start=0&count=4000" % ip
        headers = {
            'auth': auth,
            'x-api-version': api
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
    
    def GetFCoENetworks(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/fcoe-networks?start=0&count=20" % ip
        headers = {
            'auth': auth,
            'x-api-version': api
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
    
    def get_network_uri_Rack6Enc2(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        logging.info("Getting list of Fc networks")
        fc_net_inst = Networks()
        fc_net_dict = fc_net_inst.GetFcNetworks(ip, auth, api)
        fc_net_list_sorted = printDict(fc_net_dict, ['name', 'uri'])
        fcoe_net_dict = fc_net_inst.GetFCoENetworks(ip, auth, api)
        fcoe_net_list_sorted = printDict(fcoe_net_dict, ['name', 'uri'])
        eth_net_dict = fc_net_inst.GetEthernetNetworks(ip, auth, api)
        eth_net_list_sorted = printDict(eth_net_dict, ['name', 'uri'])
        for n in range (0, len(fc_net_list_sorted)):
            fc_net_name = fc_net_list_sorted[n]['name']
            fc_net_uri = fc_net_list_sorted[n]['uri']
            if fc_net_name == "BAY3_UTAH":
                fc_net_utah_bay3_uri = fc_net_uri
            elif fc_net_name == "BAY4_UTAH":
                fc_net_utah_bay4_uri = fc_net_uri
            elif fc_net_name == "BAY5_HILL":
                fc_net_hill_bay5_uri = fc_net_uri
            elif fc_net_name == "BAY6_HILL":
                fc_net_hill_bay6_uri = fc_net_uri
        for n in range (0, len(fcoe_net_list_sorted)):
            fcoe_net_name = fcoe_net_list_sorted[n]['name']
            fcoe_net_uri = fcoe_net_list_sorted[n]['uri']
            if fcoe_net_name == "BAY1_FCOE_1050":
                fcoe_net_shep_bay1_uri = fcoe_net_uri
            elif fcoe_net_name == "BAY2_FCOE_1051":
                fcoe_net_shep_bay2_uri = fcoe_net_uri
        for n in range (0, len(eth_net_list_sorted)):
            eth_net_name = eth_net_list_sorted[n]['name']
            eth_net_uri = eth_net_list_sorted[n]['uri']
            if eth_net_name == "VLAN_10":
                eth_net_shaw_vlan10_uri = eth_net_uri
            elif eth_net_name == "VLAN_30":
                eth_net_shaw_vlan30_uri = eth_net_uri
        return fcoe_net_shep_bay1_uri, fcoe_net_shep_bay2_uri, fc_net_utah_bay3_uri, fc_net_utah_bay4_uri, fc_net_hill_bay5_uri, fc_net_hill_bay6_uri, eth_net_shaw_vlan10_uri, eth_net_shaw_vlan30_uri
    
    def get_network_uri_Rack6Enc3(self, ip, auth, api):
        # type: (object, object, object) -> object
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        logging.info("Getting list of Fc networks")
        fc_net_inst = Networks()
        fc_net_dict = fc_net_inst.GetFcNetworks(ip, auth, api)
        fc_net_list_sorted = printDict(fc_net_dict, ['name', 'uri'])
        eth_net_dict = fc_net_inst.GetEthernetNetworks(ip, auth, api)
        eth_net_list_sorted = printDict(eth_net_dict, ['name', 'uri'])
        for n in range (0, len(fc_net_list_sorted)):
            fc_net_name = fc_net_list_sorted[n]['name']
            fc_net_uri = fc_net_list_sorted[n]['uri']
            if fc_net_name == "BAY3_UTAH":
                fc_net_utah_bay3_uri = fc_net_uri
            elif fc_net_name == "BAY4_UTAH":
                fc_net_utah_bay4_uri = fc_net_uri
            elif fc_net_name == "BAY5_HILL":
                fc_net_hill_bay5_uri = fc_net_uri
            elif fc_net_name == "BAY6_HILL":
                fc_net_hill_bay6_uri = fc_net_uri
            elif fc_net_name == "BAY7_OCHO":
                fc_net_ocho_bay7_uri = fc_net_uri
            elif fc_net_name == "BAY8_OCHO":
                fc_net_ocho_bay8_uri = fc_net_uri
        for n in range (0, len(eth_net_list_sorted)):
            eth_net_name = eth_net_list_sorted[n]['name']
            eth_net_uri = eth_net_list_sorted[n]['uri']
            if eth_net_name == "VLAN_10":
                eth_net_vlan10_uri = eth_net_uri
            elif eth_net_name == "VLAN_30":
                eth_net_vlan30_uri = eth_net_uri
        return eth_net_vlan10_uri, eth_net_vlan30_uri, fc_net_utah_bay3_uri, fc_net_utah_bay4_uri, fc_net_hill_bay5_uri, fc_net_hill_bay6_uri, fc_net_ocho_bay7_uri, fc_net_ocho_bay8_uri


class CreateLIG(object):

    def CreateLigRack6Enc2(slef, ip, auth, api, fcoe_net_shep_bay1_uri, fcoe_net_shep_bay2_uri, fc_net_utah_bay3_uri, fc_net_utah_bay4_uri, fc_net_hill_bay5_uri, fc_net_hill_bay6_uri, eth_net_shaw_vlan10_uri, eth_net_shaw_vlan30_uri, icm_type_sheppard_uri, icm_type_utah_uri, icm_type_hill_uri, icm_type_shaw_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/logical-interconnect-groups" %ip
        payload="{   \"type\": \"logical-interconnect-groupV8\",\r\n    \"name\": \"LIG\",\r\n    \"stackingMode\": \"Enclosure\",\r\n    \"enclosureType\": \"C7000\",\r\n    \"consistencyCheckingForInternalNetworks\": \"ExactMatch\",\r\n    \"enclosureIndexes\": [1],\r\n    \"uplinkSets\": [\r\n        {\r\n            \"networkType\": \"Ethernet\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NA\",\r\n            \"name\": \"BAY1_FCOE_VL1050\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"ethernetNetworkType\": \"Tagged\",\r\n            \"lacpTimer\": \"Short\",\r\n            \"loadBalancingMode\": \"SourceAndDestinationMac\",\r\n            \"consistencyChecking\": \"ExactMatch\",\r\n            \"failoverActiveMemberThreshold\": 4,\r\n            \"failoverBandwidthThreshold\": 50,\r\n            \"failoverType\": \"AllActiveUplinksOffline\",\r\n            \"lagPortBalance\": \"Disabled\"\r\n        },\r\n        {\r\n            \"networkType\": \"Ethernet\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NA\",\r\n            \"name\": \"BAY2_FCOE_1051\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 2\r\n                            },\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"ethernetNetworkType\": \"Tagged\",\r\n            \"lacpTimer\": \"Short\",\r\n            \"loadBalancingMode\": \"SourceAndDestinationMac\",\r\n            \"consistencyChecking\": \"ExactMatch\",\r\n            \"failoverActiveMemberThreshold\": 4,\r\n            \"failoverBandwidthThreshold\": 50,\r\n            \"failoverType\": \"AllActiveUplinksOffline\",\r\n            \"lagPortBalance\": \"Disabled\"\r\n        },\r\n        {\r\n            \"networkType\": \"FibreChannel\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NA\",\r\n            \"name\": \"BAY3_UTAH\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 3\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 18\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 3\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"consistencyChecking\": \"ExactMatch\"\r\n        },\r\n        {\r\n            \"networkType\": \"FibreChannel\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NA\",\r\n            \"name\": \"BAY4_UTAH\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 4\r\n                            },\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 18\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 4\r\n                            },\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"consistencyChecking\": \"ExactMatch\"\r\n        },\r\n        {\r\n            \"networkType\": \"FibreChannel\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NONE\",\r\n            \"name\": \"BAY5_HILL\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 19\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 5\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 5\r\n                            },\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 18\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 5\r\n                            },\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 20\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 5\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"consistencyChecking\": \"ExactMatch\"\r\n        },\r\n        {\r\n            \"networkType\": \"FibreChannel\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NONE\",\r\n            \"name\": \"BAY6_HILL\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 20\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 6\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 19\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 6\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 18\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 6\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 6\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"consistencyChecking\": \"ExactMatch\"\r\n        },\r\n        {\r\n            \"networkType\": \"Ethernet\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NA\",\r\n            \"name\": \"BAY7_SUPERSHAW_ETH_VL10\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 7\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"ethernetNetworkType\": \"Tagged\",\r\n            \"lacpTimer\": \"Short\",\r\n            \"loadBalancingMode\": \"SourceAndDestinationMac\",\r\n            \"consistencyChecking\": \"ExactMatch\",\r\n            \"failoverActiveMemberThreshold\": 4,\r\n            \"failoverBandwidthThreshold\": 50,\r\n            \"failoverType\": \"AllActiveUplinksOffline\",\r\n            \"lagPortBalance\": \"Disabled\"\r\n        },\r\n        {\r\n            \"networkType\": \"Ethernet\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NA\",\r\n            \"name\": \"BAY8_SUPERSHAW_ETH_VL30\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 8\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"ethernetNetworkType\": \"Tagged\",\r\n            \"lacpTimer\": \"Short\",\r\n            \"loadBalancingMode\": \"SourceAndDestinationMac\",\r\n            \"consistencyChecking\": \"ExactMatch\",\r\n            \"failoverActiveMemberThreshold\": 4,\r\n            \"failoverBandwidthThreshold\": 50,\r\n            \"failoverType\": \"AllActiveUplinksOffline\",\r\n            \"lagPortBalance\": \"Disabled\"\r\n        }\r\n    ],\r\n    \"interconnectMapTemplate\": {\r\n        \"interconnectMapEntryTemplates\": [\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 1\r\n                        },\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        },\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 2\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 3\r\n                        },\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 4\r\n                        },\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        },\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 5\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 6\r\n                        },\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        },\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 7\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        },\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 8\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            }\r\n        ]\r\n    }\r\n}" %(fcoe_net_shep_bay1_uri, fcoe_net_shep_bay2_uri, fc_net_utah_bay3_uri, fc_net_utah_bay4_uri, fc_net_hill_bay5_uri, fc_net_hill_bay6_uri, eth_net_shaw_vlan10_uri, eth_net_shaw_vlan30_uri, icm_type_sheppard_uri, icm_type_sheppard_uri, icm_type_utah_uri, icm_type_utah_uri, icm_type_hill_uri, icm_type_hill_uri, icm_type_shaw_uri, icm_type_shaw_uri)
        headers = {
            'auth': auth,
            'x-api-version': api,
            'content-type': "application/json"
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
    
    def CreateLigRack6Enc3(self, ip, auth, api, fc_mode, fcoe_net_super_bay1_uri, fcoe_net_super_bay2_uri, fc_net_utah_bay3_uri, fc_net_utah_bay4_uri, fc_net_hill_bay5_uri, fc_net_hill_bay6_uri, fc_net_ocho_bay7_uri, fc_net_ocho_bay8_uri, icm_type_ocho_uri, icm_type_utah_uri, icm_type_hill_uri, icm_type_shaw_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/logical-interconnect-groups" %ip
        payload = "{   \"type\": \"logical-interconnect-groupV8\",\r\n    \"name\": \"LIG\",\r\n    \"stackingMode\": \"Enclosure\",\r\n    \"enclosureType\": \"C7000\",\r\n    \"consistencyCheckingForInternalNetworks\": \"ExactMatch\",\r\n    \"enclosureIndexes\": [1],\r\n    \"uplinkSets\": [\r\n        {\r\n            \"networkType\": \"Ethernet\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NA\",\r\n            \"name\": \"BAY1-SS-VLAN10\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"ethernetNetworkType\": \"Tagged\",\r\n            \"lacpTimer\": \"Short\",\r\n            \"loadBalancingMode\": \"SourceAndDestinationMac\",\r\n            \"consistencyChecking\": \"ExactMatch\",\r\n            \"failoverActiveMemberThreshold\": 4,\r\n            \"failoverBandwidthThreshold\": 50,\r\n            \"failoverType\": \"AllActiveUplinksOffline\",\r\n            \"lagPortBalance\": \"Disabled\"\r\n        },\r\n        {\r\n            \"networkType\": \"Ethernet\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NA\",\r\n            \"name\": \"BAY2-SS-VLAN30\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 2\r\n                            },\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"ethernetNetworkType\": \"Tagged\",\r\n            \"lacpTimer\": \"Short\",\r\n            \"loadBalancingMode\": \"SourceAndDestinationMac\",\r\n            \"consistencyChecking\": \"ExactMatch\",\r\n            \"failoverActiveMemberThreshold\": 4,\r\n            \"failoverBandwidthThreshold\": 50,\r\n            \"failoverType\": \"AllActiveUplinksOffline\",\r\n            \"lagPortBalance\": \"Disabled\"\r\n        },\r\n        {\r\n            \"networkType\": \"FibreChannel\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NA\",\r\n            \"name\": \"BAY3-UTAH\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 3\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 18\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 3\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"consistencyChecking\": \"ExactMatch\"\r\n        },\r\n        {\r\n            \"networkType\": \"FibreChannel\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NA\",\r\n            \"name\": \"BAY4-UTAH\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 4\r\n                            },\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 18\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 4\r\n                            },\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"consistencyChecking\": \"ExactMatch\"\r\n        },\r\n        {\r\n            \"networkType\": \"FibreChannel\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"%s\",\r\n            \"name\": \"BAY5-HILL\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 19\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 5\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 5\r\n                            },\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 18\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 5\r\n                            },\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 20\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 5\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"consistencyChecking\": \"ExactMatch\"\r\n        },\r\n        {\r\n            \"networkType\": \"FibreChannel\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"%s\",\r\n            \"name\": \"BAY6-HILL\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 20\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 6\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 19\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 6\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 18\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 6\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 6\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"consistencyChecking\": \"ExactMatch\"\r\n        },\r\n        {\r\n            \"networkType\": \"FibreChannel\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NA\",\r\n            \"name\": \"BAY7_OCHO\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 18\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 7\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 7\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"consistencyChecking\": \"ExactMatch\"\r\n        },\r\n        {\r\n            \"networkType\": \"FibreChannel\",\r\n            \"networkUris\": [\"%s\"],\r\n            \"mode\": \"Auto\",\r\n            \"fcMode\": \"NA\",\r\n            \"name\": \"BAY8_OCHO\",\r\n            \"logicalPortConfigInfos\": [\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 18\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 8\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                },\r\n                {\r\n                    \"logicalLocation\": {\r\n                        \"locationEntries\": [\r\n                            {\r\n                                \"type\": \"Port\",\r\n                                \"relativeValue\": 17\r\n                            },\r\n                            {\r\n                                \"type\": \"Enclosure\",\r\n                                \"relativeValue\": 1\r\n                            },\r\n                            {\r\n                                \"type\": \"Bay\",\r\n                                \"relativeValue\": 8\r\n                            }\r\n                        ]\r\n                    },\r\n                    \"desiredSpeed\": \"Auto\",\r\n                    \"desiredFecMode\": \"Auto\"\r\n                }\r\n            ],\r\n            \"consistencyChecking\": \"ExactMatch\"\r\n        }\r\n    ],\r\n    \"interconnectMapTemplate\": {\r\n        \"interconnectMapEntryTemplates\": [\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 1\r\n                        },\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        },\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 2\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 3\r\n                        },\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 4\r\n                        },\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        },\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 5\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 6\r\n                        },\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        },\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 7\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            },\r\n            {\r\n                \"logicalLocation\": {\r\n                    \"locationEntries\": [\r\n                        {\r\n                            \"type\": \"Enclosure\",\r\n                            \"relativeValue\": 1\r\n                        },\r\n                        {\r\n                            \"type\": \"Bay\",\r\n                            \"relativeValue\": 8\r\n                        }\r\n                    ]\r\n                },\r\n                \"permittedInterconnectTypeUri\": \"%s\",\r\n                \"enclosureIndex\": 1\r\n            }\r\n        ]\r\n    }\r\n}\r\n" %(fcoe_net_super_bay1_uri, fcoe_net_super_bay2_uri, fc_net_utah_bay3_uri, fc_net_utah_bay4_uri, fc_net_hill_bay5_uri, fc_mode, fc_net_hill_bay6_uri, fc_mode,fc_net_ocho_bay7_uri, fc_net_ocho_bay8_uri, icm_type_shaw_uri, icm_type_shaw_uri, icm_type_utah_uri, icm_type_utah_uri, icm_type_hill_uri, icm_type_hill_uri, icm_type_ocho_uri, icm_type_ocho_uri)
        headers = {
            'auth': auth,
            'x-api-version': api,
            'content-type': "application/json"
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)


class Interconnects(object):

    def GetInterconnectTypes(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/interconnect-types" %ip
        headers = {
            'auth': auth,
            'x-api-version': api,
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)    
        return(json.loads(response.text))
    
    def GetInterconnect(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/interconnects?start=0&count=20" % ip
        headers = {
            'auth': auth,
            'x-api-version': api,
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)    
        return(json.loads(response.text))
    
    def GetInterconnectMultiEnc(self, ip, auth, api, enc_name):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/interconnects?start=0&count=20" % ip
        querystring = {"filter":"\"'enclosureName' = %s\""  %enc_name} 
        headers = {
            'auth': auth,
            'x-api-version': api,
            }
        response = requests.request("GET", url, headers=headers,params=querystring, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)    
        return(json.loads(response.text))
    
    def getHillFwVersion(self, ip, auth, api, enc_name):
        logging.info("Getting Hill fw version")
        ic_inst = Interconnects()
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
            ic_list = printDict(get_ic_dict, ['name','model', 'enclosureName', 'firmwareVersion'])
            for n, value in enumerate(ic_list):
                model = ic_list[n]['model']
                if model == "HP VC 16Gb 24-Port FC Module":
                    hill_fw_version = ic_list[n]['firmwareVersion']
                else:
                    pass
        try:
            return hill_fw_version
        except UnboundLocalError as error:
            logging.error("unable to retrieve hill version")
    
    def getUtahFwVersion(self, ip, auth, api, enc_name):
        logging.info("Getting Utah fw version")
        ic_inst = Interconnects()
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
            ic_list = printDict(get_ic_dict, ['name','model', 'enclosureName', 'firmwareVersion'])
            for n, value in enumerate(ic_list):
                model = ic_list[n]['model']
                if model == "HP VC 8Gb 24-Port FC Module":
                    utah_fw_version = ic_list[n]['firmwareVersion']
                    return utah_fw_version
                else:
                    pass
        
    def getOchoFwVersion(self, ip, auth, api, enc_name):
        logging.info("Getting Ocho fw version")
        ic_inst = Interconnects()
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
            ic_list = printDict(get_ic_dict, ['name','model', 'enclosureName', 'firmwareVersion'])
            for n, value in enumerate(ic_list):
                model = ic_list[n]['model']
                if model == "HP VC 8Gb 20-Port FC Module":
                    ocho_fw_version = ic_list[n]['firmwareVersion']
                    return ocho_fw_version
                else:
                    pass



    def getSupershawFwVersion(self, ip, auth, api, enc_name):
        logging.info("Getting Supershaw fw version")
        ic_inst = Interconnects()
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
            ic_list = printDict(get_ic_dict, ['name','model', 'enclosureName', 'firmwareVersion'])
            for n, value in enumerate(ic_list):
                model = ic_list[n]['model']
                if model == "HP VC FlexFabric-20/40 F8 Module":
                    supershaw_fw_version = ic_list[n]['firmwareVersion']
                    return supershaw_fw_version
                else:
                    pass

    def getSheppardFwVersion(self, ip, auth, api, enc_name):
        logging.info("Getting Sheppard fw version")
        ic_inst = Interconnects()
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
            ic_list = printDict(get_ic_dict, ['name','model', 'enclosureName', 'firmwareVersion'])
            for n, value in enumerate(ic_list):
                model = ic_list[n]['model']
                if model == "HP VC FlexFabric 10Gb/24-Port Module":
                    sheppard_fw_version = ic_list[n]['firmwareVersion']
                    return sheppard_fw_version
                else:
                    pass


    def getCarbonHostname(self, ip, auth, api, enc_name, ic_name):
        logging.info("Getting Carbon hostname")
        ic_inst = Interconnects()
        get_ic_dict = ic_inst.GetInterconnect(ip, auth, api, enc_name)
        ic_list = printDict(get_ic_dict, ['name', 'hostName'])
        for n, value in enumerate(ic_list):
            icm_name = ic_list[n]['name']
            if icm_name == ic_name:
                carbon_hostname = ic_list[n]['hostName']
                break
            else:
                pass
        try:
            return carbon_hostname
        except UnboundLocalError as error:
            logging.error("unable to retrieve carbon hostname")

    def CarbonHostnameUpdate(self, ip, auth, api, icm_uri, hostname):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s%s" % (ip, icm_uri)
        
        payload = "[ { \"op\": \"replace\", \"path\": \"/hostname\", \"value\": \"%s\" } ]" %hostname
        headers = {
            'x-api-version': api,
            'auth': auth,
            'content-type': "application/json"
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("PATCH", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
    
    def get_carbon_utilization(self, ip, auth, api, enc_name):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        def get_icm_util_func(ip, auth, api, icm_uri):
            logging.info("Inside function %s", sys._getframe().f_code.co_name)
            url = "https://%s%s/utilization" %(ip, icm_uri)
            headers = {
                'auth': auth,
                'x-api-version': api,
                }
            response = requests.request("GET", url, headers=headers, verify=False)
            ValidateResponse(response.status_code, response.reason, response.text)
            logging.debug(response.text)
            try:
                return(json.loads(response.text))
            except ValueError as e:
                logging.info("No JSON object to be decoded")
            except TypeError as b:
                logging.info("There was a type error")


        logging.info("Getting Interconnects")
        ic_inst = Interconnects()
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
            icm_list = printDict(get_ic_dict, ['name','uri','model','enclosureName','firmwareVersion','state'])
            perm_metric_name_configured_list = [ u'Cpu', u'Memory',u'Temperature', u'PowerAverageWatts', u'PowerPeakWatts', u'PowerMinimumWatts', u'PowerAllocatedWatts']
            perm_metric_name_monitored_list = [ u'Temperature', u'PowerAverageWatts', u'PowerPeakWatts', u'PowerMinimumWatts', u'PowerAllocatedWatts']
            for ic, value in enumerate(icm_list):
                icm_uri = icm_list[ic]['uri']
                model = icm_list[ic]['model']
                ic_name = icm_list[ic]['name']
                fw_version = icm_list[ic]['firmwareVersion']
                state = icm_list[ic]['state']
                if model == "Virtual Connect SE 16Gb FC Module for Synergy":
                    icm_util_list = get_icm_util_func(ip, auth, api, icm_uri)
                    metric_list = icm_util_list['metricList']
                    logging.testcases("Here are the utilization samples on ICM {}" .format(ic_name))
                    logging.testcases("Carbon model: {}" .format(model))
                    logging.testcases("Carbon firmware: {}" .format(fw_version))
                    logging.testcases("State of Carbon: {}" .format(state))
                    metric_name_list = []
                    if state == 'Configured':
                        for n, value in enumerate(metric_list):
                            metric_name = metric_list[n]['metricName']
                            metric_name_list.append(metric_name)
                            metric_sample = metric_list[n]['metricSamples']
                            sample = metric_sample
                            my_sample_list =  str(sample).replace('[','').replace(']','')
                            sample = my_sample_list[16:]
                            if metric_name == "Temperature" or metric_name == "PowerAverageWatts" or metric_name == "PowerPeakWatts" or metric_name == "PowerMinimumWatts" or metric_name == "PowerAllocatedWatts" or metric_name == "Cpu" or metric_name == "Memory":
                                tc = ("{}: {}" .format(metric_name, sample))
                                if sample != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                        if metric_name_list != perm_metric_name_configured_list:
                            logging.testcases("One or more metric names are missing")
                            tc = "Carbon Utilization Samples"
                            result = "Fail"
                            PassOrFail(result, tc)
                        else:
                            logging.testcases("All metric names are present")
                    elif state == 'Monitored':
                        for n, value in enumerate(metric_list):
                            metric_name = metric_list[n]['metricName']
                            metric_name_list.append(metric_name)
                            metric_sample = metric_list[n]['metricSamples']
                            sample = metric_sample
                            my_sample_list =  str(sample).replace('[','').replace(']','')
                            sample = my_sample_list[16:]
                            if metric_name == "Temperature" or metric_name == "PowerAverageWatts" or metric_name == "PowerPeakWatts" or metric_name == "PowerMinimumWatts" or metric_name == "PowerAllocatedWatts":
                                tc = ("{}: {}" .format(metric_name, sample))
                                if sample != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                        if metric_name_list != perm_metric_name_monitored_list:
                            logging.testcases("One or more metric names are missing")
                            tc = "Carbon Utilization Samples"
                            result = "Fail"
                            PassOrFail(result, tc)
                        else:
                            logging.testcases("All metric names are present")
                elif model == "Virtual Connect SE 32Gb FC Module for Synergy":
                    icm_util_list = get_icm_util_func(ip, auth, api, icm_uri)
                    metric_list = icm_util_list['metricList']
                    logging.testcases("Here are the utilization samples on ICM {}" .format(ic_name))
                    logging.testcases("Carbon model: {}" .format(model))
                    logging.testcases("Carbon firmware: {}" .format(fw_version))
                    logging.testcases("State of Carbon: {}" .format(state))
                    metric_name_list = []
                    if state == 'Configured':
                        for n, value in enumerate(metric_list):
                            metric_name = metric_list[n]['metricName']
                            metric_name_list.append(metric_name)
                            metric_sample = metric_list[n]['metricSamples']
                            sample = metric_sample
                            my_sample_list =  str(sample).replace('[','').replace(']','')
                            sample = my_sample_list[16:]
                            if metric_name == "Temperature" or metric_name == "PowerAverageWatts" or metric_name == "PowerPeakWatts" or metric_name == "PowerMinimumWatts" or metric_name == "PowerAllocatedWatts" or metric_name == "Cpu" or metric_name == "Memory":
                                tc = ("{}: {}" .format(metric_name, sample))
                                if sample != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                        if metric_name_list != perm_metric_name_configured_list:
                            logging.testcases("One or more metric names are missing")
                            tc = "Carbon Utilization Samples"
                            result = "Fail"
                            PassOrFail(result, tc)
                        else:
                            logging.testcases("All metric names are present")
                    elif state == 'Monitored':
                        for n, value in enumerate(metric_list):
                            metric_name = metric_list[n]['metricName']
                            metric_name_list.append(metric_name)
                            metric_sample = metric_list[n]['metricSamples']
                            sample = metric_sample
                            my_sample_list =  str(sample).replace('[','').replace(']','')
                            sample = my_sample_list[16:]
                            if metric_name == "Temperature" or metric_name == "PowerAverageWatts" or metric_name == "PowerPeakWatts" or metric_name == "PowerMinimumWatts" or metric_name == "PowerAllocatedWatts":
                                tc = ("{}: {}" .format(metric_name, sample))
                                if sample != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                        if metric_name_list != perm_metric_name_monitored_list:
                            logging.testcases("One or more metric names are missing")
                            tc = "Carbon Utilization Samples"
                            result = "Fail"
                            PassOrFail(result, tc)
                        else:
                            logging.testcases("All metric names are present")
                elif model == "Virtual Connect SE 16Gb FC TAA Module for Synergy":
                    icm_util_list = get_icm_util_func(ip, auth, api, icm_uri)
                    metric_list = icm_util_list['metricList']
                    logging.testcases("Here are the utilization samples on ICM {}" .format(ic_name))
                    logging.testcases("Carbon model: {}" .format(model))
                    logging.testcases("Carbon firmware: {}" .format(fw_version))
                    logging.testcases("State of Carbon: {}" .format(state))
                    metric_name_list = []
                    if state == 'Configured':
                        for n, value in enumerate(metric_list):
                            metric_name = metric_list[n]['metricName']
                            metric_name_list.append(metric_name)
                            metric_sample = metric_list[n]['metricSamples']
                            sample = metric_sample
                            my_sample_list =  str(sample).replace('[','').replace(']','')
                            sample = my_sample_list[16:]
                            if metric_name == "Temperature" or metric_name == "PowerAverageWatts" or metric_name == "PowerPeakWatts" or metric_name == "PowerMinimumWatts" or metric_name == "PowerAllocatedWatts" or metric_name == "Cpu" or metric_name == "Memory":
                                tc = ("{}: {}" .format(metric_name, sample))
                                if sample != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                        if metric_name_list != perm_metric_name_configured_list:
                            logging.testcases("One or more metric names are missing")
                            tc = "Carbon Utilization Samples"
                            result = "Fail"
                            PassOrFail(result, tc)
                        else:
                            logging.testcases("All metric names are present")
                    elif state == 'Monitored':
                        for n, value in enumerate(metric_list):
                            metric_name = metric_list[n]['metricName']
                            metric_name_list.append(metric_name)
                            metric_sample = metric_list[n]['metricSamples']
                            sample = metric_sample
                            my_sample_list =  str(sample).replace('[','').replace(']','')
                            sample = my_sample_list[16:]
                            if metric_name == "Temperature" or metric_name == "PowerAverageWatts" or metric_name == "PowerPeakWatts" or metric_name == "PowerMinimumWatts" or metric_name == "PowerAllocatedWatts":
                                tc = ("{}: {}" .format(metric_name, sample))
                                if sample != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                        if metric_name_list != perm_metric_name_monitored_list:
                            logging.testcases("One or more metric names are missing")
                            tc = "Carbon Utilization Samples"
                            result = "Fail"
                            PassOrFail(result, tc)
                        else:
                            logging.testcases("All metric names are present")
                elif model == "HPE Virtual Connect SE 16Gb FC Module for HPE Synergy":
                    icm_util_list = get_icm_util_func(ip, auth, api, icm_uri)
                    metric_list = icm_util_list['metricList']
                    logging.testcases("Here are the utilization samples on ICM {}" .format(ic_name))
                    logging.testcases("Carbon model: {}" .format(model))
                    logging.testcases("Carbon firmware: {}" .format(fw_version))
                    logging.testcases("State of Carbon: {}" .format(state))
                    metric_name_list = []
                    if state == 'Configured':
                        for n, value in enumerate(metric_list):
                            metric_name = metric_list[n]['metricName']
                            metric_name_list.append(metric_name)
                            metric_sample = metric_list[n]['metricSamples']
                            sample = metric_sample
                            my_sample_list =  str(sample).replace('[','').replace(']','')
                            sample = my_sample_list[16:]
                            if metric_name == "Temperature" or metric_name == "PowerAverageWatts" or metric_name == "PowerPeakWatts" or metric_name == "PowerMinimumWatts" or metric_name == "PowerAllocatedWatts" or metric_name == "Cpu" or metric_name == "Memory":
                                tc = ("{}: {}" .format(metric_name, sample))
                                if sample != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                        if metric_name_list != perm_metric_name_configured_list:
                            logging.testcases("One or more metric names are missing")
                            tc = "Carbon Utilization Samples"
                            result = "Fail"
                            PassOrFail(result, tc)
                        else:
                            logging.testcases("All metric names are present")
                    elif state == 'Monitored':
                        for n, value in enumerate(metric_list):
                            metric_name = metric_list[n]['metricName']
                            metric_name_list.append(metric_name)
                            metric_sample = metric_list[n]['metricSamples']
                            sample = metric_sample
                            my_sample_list =  str(sample).replace('[','').replace(']','')
                            sample = my_sample_list[16:]
                            if metric_name == "Temperature" or metric_name == "PowerAverageWatts" or metric_name == "PowerPeakWatts" or metric_name == "PowerMinimumWatts" or metric_name == "PowerAllocatedWatts":
                                tc = ("{}: {}" .format(metric_name, sample))
                                if sample != "null":
                                    result = "Pass"
                                    PassOrFail(result, tc)
                                else:
                                    result = "Fail"
                                    PassOrFail(result, tc)
                        if metric_name_list != perm_metric_name_monitored_list:
                            logging.testcases("One or more metric names are missing")
                            tc = "Carbon Utilization Samples"
                            result = "Fail"
                            PassOrFail(result, tc)
                        else:
                            logging.testcases("All metric names are present")
                else:
                    logging.info("The ICM is not a carbon")

    
    def get_carbon_downlink_port_map(self, ip, api, auth):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        ic_inst = Interconnects()
        get_interconnect_list = ic_inst.GetInterconnect(ip, auth, api)
        icm_list = printDict(get_interconnect_list, ['model', 'ports','name', 'state'])
        port_list_dict = []
        logging.info("Getting a list of downlink ports that are online\n")
        for i, value in enumerate(ic_list):
            port_list = icm_list[i]['ports']
            ic_state = icm_list[i]['state']
            if ic_state == "Configured":
                for p, value in enumerate(port_list):
                    ic_port_status_reason = port_list[p]['portStatusReason']
                    port_name = port_list[p]['portName']
                    port_type = port_list[p]['portType']
                    port_local = port_list[p]['interconnectName']
                    fc_port_properties = port_list[p]['fcPortProperties']
                    if ic_port_status_reason == "LoggedIn" and port_type == "Downlink":
                        port_list_dict.append(ic_port_status_reason)
                        port_list_dict.append(port_type)
                        port_list_dict.append(port_name)
                        port_list_dict.append(port_local)
                        fc_port_map = fc_port_properties['downlinkToUplinkPortMapping']
                        port_list_dict.append(fc_port_map)
                        fc_port_map_is_trunk_master = fc_port_properties['mappedUplinkPortIsTrunkMaster']
                        port_list_dict.append(fc_port_map_is_trunk_master)
                        logging.info("The ICM in %s with downlink port %s is mapped to UL port %s and is trunk master %s" %(port_local,port_name,fc_port_map,fc_port_map_is_trunk_master))
        return port_list_dict
    
    
    def get_fc_logins_before(self, ip, auth, api, enc_name, icm_name_rdl):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        logging.info("Getting Interconnects")
        ic_ports_uri_dict = []
        ic_inst = Interconnects()
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
            ic_ports_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName', 'ports'])
            for ic, value in enumerate(ic_ports_uri_list):
                ic_uri = ic_ports_uri_list[ic]['uri']
                ic_name = ic_ports_uri_list[ic]['name']
                ic_ports = ic_ports_uri_list[ic]['ports']
                ic_model = ic_ports_uri_list[ic]['model']
                if ic_model == "Virtual Connect SE 16Gb FC Module for Synergy" and ic_name == icm_name_rdl:
                    for p, value in enumerate(ic_ports):
                        ic_ports_uri = ic_ports[p]['uri']
                        ic_port_status_reason = ic_ports[p]['portStatusReason']
                        ic_port_properties = ic_ports[p]['fcPortProperties']
                        portName = ic_ports[p]['portName']
                        PortType = ic_ports[p]['portType']
                        PortLocal = ic_ports[p]['interconnectName']
                        if ic_port_status_reason == "LoggedIn" and PortType == "Uplink":
                            count_logins = ic_port_properties['loginsCount']
                            if count_logins == 4:
                                ic_ports_uri_dict.append(ic_ports_uri)
    
                elif ic_model == "Virtual Connect SE 32Gb FC Module for Synergy" and ic_name == icm_name_rdl:
                    for p, value in enumerate(ic_ports):
                        ic_ports_uri = ic_ports[p]['uri']
                        ic_port_status_reason = ic_ports[p]['portStatusReason']
                        ic_port_properties = ic_ports[p]['fcPortProperties']
                        portName = ic_ports[p]['portName']
                        PortType = ic_ports[p]['portType']
                        PortLocal = ic_ports[p]['interconnectName']
                        if ic_port_status_reason == "LoggedIn" and PortType == "Uplink":
                            count_logins = ic_port_properties['loginsCount']
                            if count_logins == 4:
                                ic_ports_uri_dict.append(ic_ports_uri)
        return ic_ports_uri_dict
    
    def get_fc_logins_after(self, ip, auth, api, enc_name, icm_name_rdl):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        logging.info("Getting Interconnects")
        ic_ports_uri_dict = []
        ic_inst = Interconnects()
        for name in enc_name:
            get_ic_dict = ic_inst.GetInterconnect(ip, auth, api)
            ic_ports_uri_list = printDict(get_ic_dict, ['name', 'uri', 'model', 'enclosureName', 'ports'])
            for ic, value in enumerate(ic_ports_uri_list):
                ic_uri = ic_ports_uri_list[ic]['uri']
                ic_name = ic_ports_uri_list[ic]['name']
                ic_ports = ic_ports_uri_list[ic]['ports']
                ic_model = ic_ports_uri_list[ic]['model']
                if ic_model == "Virtual Connect SE 16Gb FC Module for Synergy" and ic_name == icm_name_rdl:
                    for p, value in enumerate(ic_ports):
                        ic_ports_uri = ic_ports[p]['uri']
                        ic_port_status_reason = ic_ports[p]['portStatusReason']
                        ic_port_properties = ic_ports[p]['fcPortProperties']
                        portName = ic_ports[p]['portName']
                        PortType = ic_ports[p]['portType']
                        PortLocal = ic_ports[p]['interconnectName']
                        if ic_port_status_reason == "LoggedIn" and PortType == "Uplink":
                            count_logins = ic_port_properties['loginsCount']
                            if count_logins == 1:
                                ic_ports_uri_dict.append(ic_ports_uri)

                elif ic_model == "Virtual Connect SE 32Gb FC Module for Synergy" and ic_name == icm_name_rdl:
                    for p, value in enumerate(ic_ports):
                        ic_ports_uri = ic_ports[p]['uri']
                        ic_port_status_reason = ic_ports[p]['portStatusReason']
                        ic_port_properties = ic_ports[p]['fcPortProperties']
                        portName = ic_ports[p]['portName']
                        PortType = ic_ports[p]['portType']
                        PortLocal = ic_ports[p]['interconnectName']
                        if ic_port_status_reason == "LoggedIn" and PortType == "Uplink":
                            count_logins = ic_port_properties['loginsCount']
                            if count_logins == 1:
                                ic_ports_uri_dict.append(ic_ports_uri)
        return ic_ports_uri_dict


class LogicalEnclosure(object):

    def GetLogicalEnclosure(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/logical-enclosures" %ip
        headers = {
            'auth': auth,
            'x-api-version': api,
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)    
        return(json.loads(response.text))
        
    def GenerateLESupportDump(self, ip, auth, api, le_uri, support_dump_name):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s%s/support-dumps" %(ip, le_uri)
        payload = "{\r\n    \"errorCode\": \"%s\",\r\n    \"excludeApplianceDump\": false\r\n}" %(support_dump_name)
        headers = {
        'Content-Type': 'application/json',
        'x-api-version': api,
            'auth': auth
        }
        logging.debug("url: %s" % url)
        logging.debug("payload: %s" % payload)
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        logging.debug("response: %s" % response)
        ValidateResponse(response.status_code, response.reason, response.headers)
        logging.debug(response.headers)
        return(response.headers)
        
    def DownloadLEsupportDump(self, ip, auth, api, encrypted, support_dump_link, eagle):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        TimeStamp = time.strftime("%Y%m%d_%H%M%S")
        file_name = (TimeStamp +'_LE_SupportDump_' + eagle + '_' + encrypted +'.sdmp')
        folder_path = os.path.join('C:', os.sep, 'SupportDumps', '{}') .format(file_name)
        url = "https://%s%s" %(ip, support_dump_link)
        headers = {
            'auth': auth,
            'x-api-version': api
            }
        with open (folder_path, 'wb') as f:
            print "Downloading %s" % file_name
            response = requests.get(url, headers=headers, stream=True, verify=False)
            total_length = response.headers.get('content-length')
            ValidateResponse(response.status_code, response.reason, response.text)
            if total_length is None: # no content length header
                f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )
                    sys.stdout.flush()
        return folder_path, file_name
        
    def Create_le_support_dump(self, ip, auth, api, encrypted, eagle):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        support_dump_name = eagle
        logging.info("Getting Logical Enclosure")
        le_inst = LogicalEnclosure()
        le_dict = le_inst.GetLogicalEnclosure(ip, auth, api)
        le_list_uri = printDict(le_dict, ['uri'])
        le_uri = le_list_uri[0]['uri']
        
        headers_dict = le_inst.GenerateLESupportDump(ip, auth, api, le_uri, encrypted, support_dump_name)
        task_uri = headers_dict['Location']
        logging.info("The support dump task is: {}" .format(task_uri))
        countdown(0, 5)
        task_dict = get_task(ip, auth, api, task_uri)
        task_state = task_dict['taskState']
        while task_state == 'Running':
            task_dict = get_task(ip, auth, api, task_uri)
            task_state = task_dict['taskState']
            logging.info("The state of support dump task: {}" .format(task_state))
            if task_state == 'Running':
                print "Support Dump is being created"
            elif task_state == 'Completed':
                support_dump_link = task_dict['associatedResource']['resourceUri']
                logging.info("The support dump has been created, downloading support dump.")
                sd_file = le_inst.DownloadLEsupportDump(ip, auth, api, encrypted, support_dump_link, eagle)
                break
            countdown(3, 0)
        return sd_file


class LogicalInterconnectGroup(object):

    def GetListOfLIGs(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/logical-interconnect-groups" %ip
        headers = {
            'auth': auth,
            'x-api-version': api,
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))


class Servers(object):

    def ServerProfiles(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/server-profiles" % ip
        headers = {
            'x-api-version': api,
            'auth': auth
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
    
    def ServerProfilesTemplates(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/server-profile-templates" % ip
        headers = {
            'x-api-version': api,
            'auth': auth
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
    
    def ServerHW(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/server-hardware" % ip
        headers = {
            'auth': auth,
            'x-api-version': api
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
    
    def server_hw_firmware_inventory(self, ip, auth, api, server_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s%s/firmware" %(ip, server_uri)
        headers = {
            'auth': auth,
            'x-api-version': api
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))

    def server_wwwn_wwpn(self, wwnn1_start, wwpn1_start, wwnn2_start, wwpn2_start):
        wwnn1 = [wwnn1_start+str(i) for i in range(80,100,2)]
        wwpn1 = [wwpn1_start+str(i) for i in range(80,100,2)]
        wwnn2 = [wwnn2_start+str(i) for i in range(81,100,2)]
        wwpn2 = [wwpn2_start+str(i) for i in range(81,100,2)]
        return wwnn1, wwpn1, wwnn2, wwpn2
    
    def server_profile_config_eagle3(self):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        agency = ['NASA','DEFENSE DEPT','NSA','STATE DEPT','TREASURY DEPT','CIA','COMMERCE DEPT','EDUCATION DEPT','CONGRESS','SUPREME COURT','AUSTIN','DALLAS','HOUSTON','JERUSALEM','LOS ANGELES','FRANKFURT','LONDON','MIAMI','TOKYO','SYDNEY','DENVER']
        sp_names_start = 'Server Profile '
        sp_name = [sp_names_start+str(i) for i in range(1,25,1)]
        SP_desc = 'Server Profile for '
        ServerProfilesDescriptions = [SP_desc+str(i) for i in (agency)]
        sp_descr = sorted(ServerProfilesDescriptions)
        ID1_start = ''
        id_1 = [ID1_start+str(i) for i in range(1,40,2)]
        ID2_start = ''
        id_2 = [ID2_start+str(i) for i in range(2,40,2)]
        ID3_start = ''
        id_3 = [ID3_start+str(i) for i in range(30,70,2)]
        ID4_start = ''
        id_4 = [ID4_start+str(i) for i in range(31,70,2)]
        ID5_start = ''
        id_5 = [ID5_start+str(i) for i in range(60,100,2)]
        ID6_start = ''
        id_6 = [ID6_start+str(i) for i in range(61,100,2)]
        return sp_name, sp_descr, id_1, id_2, id_3, id_4, id_5, id_6

    def server_profile_config_eagle30(self):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        agency = ['NASA','DEFENSE DEPT','NSA','STATE DEPT','TREASURY DEPT','CIA','COMMERCE DEPT','EDUCATION DEPT','CONGRESS','SUPREME COURT','AUSTIN','DALLAS','HOUSTON','JERUSALEM','LOS ANGELES','FRANKFURT','LONDON','MIAMI','TOKYO','SYDNEY','DENVER']
        sp_names_start = 'Server Profile '
        sp_name = [sp_names_start+str(i) for i in range(1,25,1)]
        SP_desc = 'Server Profile for '
        ServerProfilesDescriptions = [SP_desc+str(i) for i in (agency)]
        sp_descr = sorted(ServerProfilesDescriptions)
        ID1_start = ''
        id_1 = [ID1_start+str(i) for i in range(1,40,2)]
        ID2_start = ''
        id_2 = [ID2_start+str(i) for i in range(2,40,2)]
        ID3_start = ''
        id_3 = [ID3_start+str(i) for i in range(30,70,2)]
        ID4_start = ''
        id_4 = [ID4_start+str(i) for i in range(31,70,2)]
        ID5_start = ''
        id_5 = [ID5_start+str(i) for i in range(60,100,2)]
        ID6_start = ''
        id_6 = [ID6_start+str(i) for i in range(61,100,2)]
        ID7_start = ''
        id_7 = [ID7_start+str(i) for i in range(101,120,2)]
        return sp_name, sp_descr, id_1, id_2, id_3, id_4, id_5, id_6, id_7


    def server_profile_config(self):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        agency = ['NASA','DEFENSE DEPT','NSA','STATE DEPT','TREASURY DEPT','CIA','COMMERCE DEPT','EDUCATION DEPT','CONGRESS','SUPREME COURT']
        sp_names_start = 'Server Profile '
        sp_names_list = [sp_names_start+str(i) for i in range(1,10,1)]
        sp_names = sorted(sp_names_list)
        SP_desc = 'Server Profile for '
        ServerProfilesDescriptions = [SP_desc+str(i) for i in (agency)]
        sp_descr = sorted(ServerProfilesDescriptions)
        id1_start = ''
        id_1 = [id1_start+str(i) for i in range(1,50,2)]
        id2_start = ''
        id_2 = [id2_start+str(i) for i in range(2,50,2)]
        return sp_names, sp_descr, id_1, id_2
        
    def server_wwnn_start_wwpn_start(self, enc):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        if enc == 'Eagle155':
            array_wwpn1 = '21:70:00:c0:ff:1e:85:70'
            array_wwpn2 = '25:70:00:c0:ff:1e:85:70'
            wwnn1_start = '20:00:70:10:6F:76:B5:'
            wwpn1_start = '10:00:70:10:6F:76:B5:'
            wwnn2_start = '20:00:70:10:6F:76:B5:'
            wwpn2_start = '10:00:70:10:6F:76:B5:'
        elif enc == 'Eagle21':
            array_wwpn1 = '20:70:00:c0:ff:1e:85:70'
            array_wwpn2 = '24:70:00:c0:ff:1e:85:70'
            wwnn1_start = '20:00:70:11:6F:76:B5:'
            wwpn1_start = '10:00:70:11:6F:76:B5:'
            wwnn2_start = '20:00:70:11:6F:76:B5:'
            wwpn2_start = '10:00:70:11:6F:76:B5:'
        elif enc == 'Eagle28':
            array_wwpn1 = "21:70:00:c0:ff:25:b0:79"
            array_wwpn2 = "25:70:00:c0:ff:25:b0:79"
            wwnn1_start = '20:00:70:12:6F:76:B5:'
            wwpn1_start = '10:00:70:12:6F:76:B5:'
            wwnn2_start = '20:00:70:12:6F:76:B5:'
            wwpn2_start = '10:00:70:12:6F:76:B5:'
        elif enc == 'Eagle136':
            array_wwpn1 = '20:02:00:02:ac:01:cd:ec'
            array_wwpn2 = '21:02:00:02:ac:01:cd:ec'
            wwnn1_start = '20:00:70:13:6F:76:B5:'
            wwpn1_start = '10:00:70:13:6F:76:B5:'
            wwnn2_start = '20:00:70:13:6F:76:B5:'
            wwpn2_start = '10:00:70:13:6F:76:B5:'
        elif enc == 'Eagle20':
            array_wwpn1 = '20:70:00:c0:ff:1e:85:70'
            array_wwpn2 = '24:70:00:c0:ff:1e:85:70'
            wwnn1_start = '20:00:70:14:6F:76:B5:'
            wwpn1_start = '10:00:70:14:6F:76:B5:'
            wwnn2_start = '20:00:70:14:6F:76:B5:'
            wwpn2_start = '10:00:70:14:6F:76:B5:'
        elif enc == 'Eagle40':
            array_wwpn1 = '20:70:00:c0:ff:1e:85:70'
            array_wwpn2 = '24:70:00:c0:ff:1e:85:70'
            wwnn1_start = '20:00:70:15:6F:76:B5:'
            wwpn1_start = '10:00:70:15:6F:76:B5:'
            wwnn2_start = '20:00:70:15:6F:76:B5:'
            wwpn2_start = '10:00:70:15:6F:76:B5:'
        elif enc == 'Eagle13':
            array_wwpn1 = '20:70:00:c0:ff:1e:85:70'
            array_wwpn2 = '24:70:00:c0:ff:1e:85:70'
            wwnn1_start = '20:00:70:16:6F:76:B5:'
            wwpn1_start = '10:00:70:16:6F:76:B5:'
            wwnn2_start = '20:00:70:16:6F:76:B5:'
            wwpn2_start = '10:00:70:16:6F:76:B5:'
            
        return array_wwpn1, array_wwpn2, wwnn1_start, wwpn1_start, wwnn2_start, wwpn2_start
    
    def allocate_target_wwpn(self, icm):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        if icm == 'nitro':
            array_dict = {'Q1:1': '56:c9:ce:90:8f:75:25:01', 'Q1:2': '56:c9:ce:90:8f:75:25:0d', 'Q2:1': '56:c9:ce:90:8f:75:25:05', 'Q2:2': '56:c9:ce:90:8f:75:25:11'}
        elif icm == 'potash':
            array_dict = {'Q1:1': '56:c9:ce:90:8f:75:25:04', 'Q1:2': '56:c9:ce:90:8f:75:25:10', 'Q2:1': '56:c9:ce:90:8f:75:25:07', 'Q2:2': '56:c9:ce:90:8f:75:25:13'}
        
        for i in (array_dict):
            if i == 'Q1:1':
                port1_q1_1 = array_dict[i]
            elif i == 'Q1:2':
                port1_q1_2 = array_dict[i]
            elif i == 'Q2:1':
                port2_q2_1 = array_dict[i]
            elif i == 'Q2:2':
                port2_q2_2 = array_dict[i]
    
        return port1_q1_1, port1_q1_2, port2_q2_1, port2_q2_2


class CreateFibreChannelNetworks(object):

    def CreateFcNetwork(self, ip, auth, api, net):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/fc-networks" % ip
        payload = "{\r\n    \"name\" : \"%s\",\r\n    \"connectionTemplateUri\" : null,\r\n    \"linkStabilityTime\" : \"30\",\r\n    \"autoLoginRedistribution\" : true,\r\n    \"fabricType\" : \"FabricAttach\",\r\n    \"type\" : \"fc-networkV4\"\r\n}" % (net)
        headers = {
            'x-api-version': api,
            'auth': auth,
            'content-type': "application/json"
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)    
        
    def CreateFcNetworkDA(self, ip, auth, api, net):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/fc-networks" % ip
        payload = "{\r\n    \"name\" : \"%s\",\r\n    \"connectionTemplateUri\" : null,\r\n    \"linkStabilityTime\" : \"30\",\r\n    \"autoLoginRedistribution\" : true,\r\n    \"fabricType\" : \"DirectAttach\",\r\n    \"type\" : \"fc-networkV4\"\r\n}" % (net)
        headers = {
            'x-api-version': api,
            'auth': auth,
            'content-type': "application/json"
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)    


class CreateEthernetNetworks(object):

    def create_ethernet_network(self, ip, auth, api, net):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/ethernet-networks" % ip
        payload = "{\r\n    \"purpose\" : \"General\",\r\n    \"name\" : \"%s\",\r\n    \"smartLink\" : true,\r\n    \"privateNetwork\" : false,\r\n    \"connectionTemplateUri\" : null,\r\n    \"ethernetNetworkType\" : \"Untagged\",\r\n    \"type\" : \"ethernet-networkV4\"\r\n}\r\n" % (net)
        headers = {
            'x-api-version': api,
            'auth': auth,
            'content-type': "application/json"
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)    
    
    def create_eth_tagged_network(self, ip, auth, api, net):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/ethernet-networks" % ip
        payload = "{\r\n    \"vlanId\" : %s,\r\n    \"purpose\" : \"General\",\r\n    \"name\" : \"VLAN_%s\",\r\n    \"smartLink\" : true,\r\n    \"privateNetwork\" : false,\r\n    \"connectionTemplateUri\" : null,\r\n    \"ethernetNetworkType\" : \"Tagged\",\r\n    \"type\" : \"ethernet-networkV4\"\r\n}" % (net, net)
        headers = {
            'x-api-version': api,
            'auth': auth,
            'content-type': "application/json"
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
    
    def create_fcoe_network(self, ip, auth, api, net_name, vlanID):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/fcoe-networks" % ip
        payload = "{\r\n  \"name\" : \"%s\",\r\n  \"vlanId\" : \"%s\",\r\n  \"connectionTemplateUri\" : null,\r\n  \"type\" : \"fcoe-networkV4\"\r\n}" %(net_name, vlanID)
        headers = {
            'x-api-version': api,
            'auth': auth,
            'content-type': "application/json"
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)


class CreateEnclosureGroup(object):

    def CreateEgTBird(self, ip, auth, api, lig_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/enclosure-groups" %ip
        payload = "{\r\n\t\"powerMode\": \"RedundantPowerSupply\",\r\n\t\"name\": \"EG1\",\r\n\t\"enclosureCount\": \"1\",\r\n\t\"ipAddressingMode\": \"DHCP\",\r\n\t\"osDeploymentSettings\": {\r\n\t\t\"deploymentModeSettings\": null,\r\n\t\t\"manageOSDeployment\": false\r\n\t},\r\n\t\"interconnectBayMappings\": [{\r\n\t\t\"enclosureIndex\": \"1\",\r\n\t\t\"interconnectBay\": \"1\",\r\n\t\t\"logicalInterconnectGroupUri\": \"%s\"\r\n\t}, {\r\n\t\t\"enclosureIndex\": \"1\",\r\n\t\t\"interconnectBay\": \"4\",\r\n\t\t\"logicalInterconnectGroupUri\": \"%s\"\r\n\t}\r\n]\r\n\r\n}" %(lig_uri, lig_uri)
        headers = {
            'auth': auth,
            'x-api-version': api,
            'content-type': "application/json",
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)    
        return(json.loads(response.text))
    
    def CreateEgRack6Enc2(self, ip, auth, api, lig_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/enclosure-groups" %ip
        payload = "{ \"name\": \"EG1\",\r\n  \"ipAddressingMode\": \"External\",\r\n  \"ipv6AddressingMode\": \"External\",\r\n  \"ambientTemperatureMode\": \"Standard\",\r\n  \"enclosureCount\": 1,\r\n  \"interconnectBayMappings\": [\r\n        {\r\n            \"interconnectBay\": 1,\r\n            \"logicalInterconnectGroupUri\": \"%s\"\r\n        },\r\n        {\r\n            \"interconnectBay\": 2,\r\n            \"logicalInterconnectGroupUri\": \"%s\"\r\n        },\r\n        {\r\n            \"interconnectBay\": 3,\r\n            \"logicalInterconnectGroupUri\": \"%s\"\r\n        },\r\n        {\r\n            \"interconnectBay\": 4,\r\n            \"logicalInterconnectGroupUri\": \"%s\"\r\n        },\r\n        {\r\n            \"interconnectBay\": 5,\r\n            \"logicalInterconnectGroupUri\": \"%s\"\r\n        },\r\n        {\r\n            \"interconnectBay\": 6,\r\n            \"logicalInterconnectGroupUri\": \"%s\"\r\n        },\r\n        {\r\n            \"interconnectBay\": 7,\r\n            \"logicalInterconnectGroupUri\": \"%s\"\r\n        },\r\n        {\r\n            \"interconnectBay\": 8,\r\n            \"logicalInterconnectGroupUri\": \"%s\"\r\n        }\r\n    ]\r\n\r\n}" %(lig_uri, lig_uri, lig_uri, lig_uri, lig_uri, lig_uri, lig_uri, lig_uri,)
        headers = {
            'auth': auth,
            'x-api-version': api,
            'content-type': "application/json"
            }
        
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))


class CreateLogicalEnclosure(object):

    def CreateLE(self, ip, auth, api, enc_uri, enc_grp_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/logical-enclosures" %ip
        payload = "{\r\n   \"name\" : \"LE\",\r\n   \"enclosureUris\":\r\n   [\r\n                \"%s\"\r\n   ],\r\n  \"enclosureGroupUri\": \"%s\", \r\n   \"firmwareBaselineUri\" : null,\r\n   \"forceInstallFirmware\" : false\r\n}" %(enc_uri, enc_grp_uri)
        headers = {
            'auth': auth,
            'x-api-version': api,
            'content-type': "application/json",
            'accept-language': "en-US",
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)


class UpdateLogicalEnclosure(object):

    def LeUpdateFromGroup(self, ip, auth, api, le_uri):
        url = "https://%s%s/updateFromGroup" %(ip, le_uri)
        headers = {
            'auth': auth,
            'x-api-version': api
            }
        logging.debug("url: %s" % url)
        response = requests.request("PUT", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)


class IsResourceDeleted(object):

    def IsSPDeleted(self,ip,auth,api):
        GetSp = Servers()
        GetSpList = GetSp.ServerProfiles(ip, auth, api)
        count = GetSpList['count']
        if count == 0:
            return True
        else:
            return False
    
    def IsSPTDeleted(self,ip,auth,api):
        GetSpt = Servers()
        GetSptList = GetSpt.ServerProfilesTemplates(ip,auth,api)
        count = GetSptList['count']
        if count == 0:
            return True
        else:
            return False
    
    def IsEgDeleted(self,ip,auth,api):
        enc_instance = Enclosures()
        EncGrpDict = enc_instance.EncGroup(ip, auth, api)
        count = EncGrpDict['count']
        if count == 0:
            return True
        else:
            return False
    
    def IsLeDeleted(self,ip,auth,api):
        GetLE = LogicalEnclosure()
        LeList = GetLE.GetLogicalEnclosure(ip, auth, api)
        count = LeList['count']
        if count == 0:
            return True
        else:
            return False
    
    def IsLIGDeleted(self,ip,auth,api):
        Ligs = LogicalInterconnectGroup()
        ListOfLig = Ligs.GetListOfLIGs(ip, auth, api)
        count = ListOfLig['count']
        if count == 0:
            return True
        else:
            return False
    
    def IsFcNetDeleted(self,ip,auth,api):
        FcNetworks = Networks()
        FcNetworksList = FcNetworks.GetFcNetworks(ip, auth, api)
        count = FcNetworksList['count']
        if count == 0:
            return True
        else:
            return False
    
    def IsEthernetDeleted(self,ip,auth,api):
        EthNetworks = Networks()
        EthNetworksList = EthNetworks.GetEthernetNetworks(ip, auth, api)
        count = EthNetworksList['count']
        if count == 0:
            return True
        else:
            return False
    
    def IsFCoEDeleted(self,ip,auth,api):
        FCoENetworks = Networks()
        FCoENetworksList = FCoENetworks.GetFCoENetworks(ip, auth, api)
        count = FCoENetworksList['count']
        if count == 0:
            return True
        else:
            return False
    
    def IsNetworkSetDeleted(self, ip, auth, api):
        network_set_impl = NetworkSets()
        network_set_list = network_set_impl.GetNetworkSets(ip, auth, api)
        count = network_set_list['count']
        if count == 0:
            return True
        else:
            return False


class CreateServerProfile(object):

    def CreateServerProfileRack6Enc3(self, ip, auth, api, sp_name, server_hw_uri, enc_grp_uri, fc_net_hill_bay5_uri,  fc_net_hill_bay6_uri, eth_net_vlan10_uri, eth_net_vlan30_uri, id_1, id_2, id_3, id_4):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/server-profiles" %ip
        querystring = {"force":"ignoreServerHealth"}
        payload = "{\r\n    \"type\":\"ServerProfileV12\",\r\n    \"name\":\"%s\",\r\n    \"serverHardwareUri\":\"%s\",\r\n    \"enclosureGroupUri\":\"%s\",\r\n    \"affinity\" : \"Bay\",\r\n    \"macType\" : \"Physical\",\r\n    \"serialNumberType\" : \"Physical\",\r\n    \"wwnType\" : \"Physical\",\r\n    \"hideUnusedFlexNics\" : true,\r\n    \"connectionSettings\": {\r\n        \"connections\": [{\r\n                \"id\": \"%s\",\r\n                \"name\":\"BAY5-HILL\",\r\n                \"functionType\": \"FibreChannel\",\r\n                \"portId\": \"Auto\",\r\n                \"wwpnType\":\"Physical\",\r\n                \"networkUri\": \"%s\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\":\"BAY6-HILL\",\r\n                \"functionType\": \"FibreChannel\",\r\n                \"portId\": \"Auto\",\r\n                \"wwpnType\":\"Physical\",\r\n                \"networkUri\": \"%s\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\": \"SUPERSHAW_BAY1_VL10\",\r\n                \"functionType\": \"Ethernet\",\r\n                \"networkUri\": \"%s\",\r\n                \"portId\": \"Flb 1:1-a\",\r\n                \"macType\": \"Physical\",\r\n                \"wwpnType\": \"Physical\",\r\n                \"requestedMbps\": \"2500\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\": \"SUPERSHAW_BAY2_VL30\",\r\n                \"functionType\": \"Ethernet\",\r\n                \"networkUri\": \"%s\",\r\n                \"portId\": \"Flb 1:2-a\",\r\n                \"macType\": \"Physical\",\r\n                \"wwpnType\": \"Physical\",\r\n                \"requestedMbps\": \"2500\"\r\n            }\r\n        ]\r\n    },\r\n    \"bootMode\": {\r\n        \"manageMode\": true,\r\n        \"mode\": \"UEFI\",\r\n        \"pxeBootPolicy\": \"Auto\",\r\n        \"secureBoot\": \"Disabled\"\r\n    }\r\n}\r\n" %(sp_name, server_hw_uri, enc_grp_uri, id_1, fc_net_hill_bay5_uri, id_2, fc_net_hill_bay6_uri,  id_3 , eth_net_vlan10_uri, id_4, eth_net_vlan30_uri)
        headers = {
            'auth': auth,
            'x-api-version': api,
            'content-type': "application/json"
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, params=querystring, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
    
    def CreateServerProfileRack6Enc3Bay2(self, ip, auth, api, sp_name, server_hw_uri, enc_grp_uri, fc_net_utah_bay3_uri, fc_net_utah_bay4_uri, fc_net_hill_bay5_uri, fc_net_hill_bay6_uri, eth_net_vlan10_uri, eth_net_vlan30_uri, id_1, id_2, id_3, id_4, id_5, id_6):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/server-profiles" %ip
        querystring = {"force":"ignoreServerHealth"}
        payload = "{\r\n    \"type\":\"ServerProfileV12\",\r\n    \"name\":\"%s\",\r\n    \"serverHardwareUri\":\"%s\",\r\n    \"enclosureGroupUri\":\"%s\",\r\n    \"affinity\" : \"Bay\",\r\n    \"macType\" : \"Physical\",\r\n    \"serialNumberType\" : \"Physical\",\r\n    \"wwnType\" : \"Physical\",\r\n    \"hideUnusedFlexNics\" : true,\r\n    \"connectionSettings\": {\r\n        \"connections\": [{\r\n                \"id\": \"%s\",\r\n                \"name\":\"BAY3_UTAH\",\r\n                \"functionType\": \"FibreChannel\",\r\n                \"portId\": \"Auto\",\r\n                \"wwpnType\":\"Physical\",\r\n                \"networkUri\": \"%s\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\":\"BAY4_UTAH\",\r\n                \"functionType\": \"FibreChannel\",\r\n                \"portId\": \"Auto\",\r\n                \"wwpnType\":\"Physical\",\r\n                \"networkUri\": \"%s\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\":\"BAY5-HILL\",\r\n                \"functionType\": \"FibreChannel\",\r\n                \"portId\": \"Auto\",\r\n                \"wwpnType\":\"Physical\",\r\n                \"networkUri\": \"%s\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\":\"BAY6-HILL\",\r\n                \"functionType\": \"FibreChannel\",\r\n                \"portId\": \"Auto\",\r\n                \"wwpnType\":\"Physical\",\r\n                \"networkUri\": \"%s\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\": \"SUPERSHAW_BAY1_VL10\",\r\n                \"functionType\": \"Ethernet\",\r\n                \"networkUri\": \"%s\",\r\n                \"portId\": \"Flb 1:1-a\",\r\n                \"macType\": \"Physical\",\r\n                \"wwpnType\": \"Physical\",\r\n                \"requestedMbps\": \"2500\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\": \"SUPERSHAW_BAY2_VL30\",\r\n                \"functionType\": \"Ethernet\",\r\n                \"networkUri\": \"%s\",\r\n                \"portId\": \"Flb 1:2-a\",\r\n                \"macType\": \"Physical\",\r\n                \"wwpnType\": \"Physical\",\r\n                \"requestedMbps\": \"2500\"\r\n            }\r\n        ]\r\n    },\r\n    \"bootMode\": {\r\n        \"manageMode\": true,\r\n        \"mode\": \"UEFI\",\r\n        \"pxeBootPolicy\": \"Auto\",\r\n        \"secureBoot\": \"Disabled\"\r\n    }\r\n}\r\n" %(sp_name, server_hw_uri, enc_grp_uri, id_1, fc_net_utah_bay3_uri, id_2, fc_net_utah_bay4_uri, id_3, fc_net_hill_bay5_uri, id_4, fc_net_hill_bay6_uri, id_5 , eth_net_vlan10_uri, id_6, eth_net_vlan30_uri)
        headers = {
            'auth': auth,
            'x-api-version': api,
            'content-type': "application/json"
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, params=querystring, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
    
    def CreateServerProfileRack6Enc2(self, ip, auth, api, sp_name, server_hw_uri, enc_grp_uri, boot_mode, fc_net_utah_bay3_uri, fc_net_utah_bay4_uri, fc_net_hill_bay5_uri, fc_net_hill_bay6_uri, fcoe_net_shep_bay1_uri, fcoe_net_shep_bay2_uri, id_1, id_2, id_3, id_4, id_5, id_6):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/server-profiles" %ip
        querystring = {"force":"ignoreServerHealth"}
        payload = "{\r\n    \"type\":\"ServerProfileV12\",\r\n    \"name\":\"%s\",\r\n    \"serverHardwareUri\":\"%s\",\r\n    \"enclosureGroupUri\":\"%s\",\r\n    \"affinity\" : \"Bay\",\r\n    \"macType\" : \"Physical\",\r\n    \"serialNumberType\" : \"Physical\",\r\n    \"wwnType\" : \"Physical\",\r\n    \"hideUnusedFlexNics\" : true,\r\n    \"connectionSettings\": {\r\n        \"connections\": [{\r\n                \"id\": \"%s\",\r\n                \"name\":\"BAY3-UTAH\",\r\n                \"functionType\": \"FibreChannel\",\r\n                \"portId\": \"Auto\",\r\n                \"wwpnType\":\"Physical\",\r\n                \"networkUri\": \"%s\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\":\"BAY4-UTAH\",\r\n                \"functionType\": \"FibreChannel\",\r\n                \"portId\": \"Auto\",\r\n                \"wwpnType\":\"Physical\",\r\n                \"networkUri\": \"%s\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\":\"BAY5-HILL\",\r\n                \"functionType\": \"FibreChannel\",\r\n                \"portId\": \"Auto\",\r\n                \"wwpnType\":\"Physical\",\r\n                \"networkUri\": \"%s\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\":\"BAY6-HILL\",\r\n                \"functionType\": \"FibreChannel\",\r\n                \"portId\": \"Auto\",\r\n                \"wwpnType\":\"Physical\",\r\n                \"networkUri\": \"%s\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\": \"SHEPPERD-BAY1-FCOE-VL1050\",\r\n                \"functionType\": \"FibreChannel\",\r\n                \"networkUri\": \"%s\",\r\n                \"portId\": \"Flb 1:1-b\",\r\n                \"macType\": \"Physical\",\r\n                \"wwpnType\": \"Physical\",\r\n                \"requestedMbps\": \"2500\"\r\n            },\r\n            {\r\n                \"id\": \"%s\",\r\n                \"name\": \"SHEPPERD-BAY2-FCOE-VL1051\",\r\n                \"functionType\": \"FibreChannel\",\r\n                \"networkUri\": \"%s\",\r\n                \"portId\": \"Flb 1:2-b\",\r\n                \"macType\": \"Physical\",\r\n                \"wwpnType\": \"Physical\",\r\n                \"requestedMbps\": \"2500\"\r\n            }\r\n        ]\r\n    },\r\n    \"bootMode\": {\r\n        \"manageMode\": true,\r\n        \"mode\": \"%s\",\r\n        \"pxeBootPolicy\": null,\r\n        \"secureBoot\": \"Disabled\"\r\n    }\r\n}" %(sp_name, server_hw_uri, enc_grp_uri, id_1, fc_net_utah_bay3_uri, id_2, fc_net_utah_bay4_uri, id_3, fc_net_hill_bay5_uri, id_4, fc_net_hill_bay6_uri, id_5 , fcoe_net_shep_bay1_uri, id_6, fcoe_net_shep_bay2_uri, boot_mode)
        headers = {
            'auth': auth,
            'x-api-version': api,
            'content-type': "application/json"
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("POST", url, data=payload, headers=headers, params=querystring, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
    

class PowerOffOnServers(object):

    def power_off_servers(self, ip, auth, api):
        logging.info("Getting Server HW and Profiles")
        srvr_power_check_inst = CheckServerPower()
        server_hw_profiles_inst = Servers()
        server_hw_list = server_hw_profiles_inst.ServerHW(ip, auth, api)
        server_hw_name_uri_model = printDict(server_hw_list, ['name', 'uri', 'model'])
        logging.info("Getting Server Powerstate")
        srvr_hw_power_state = printDict(server_hw_list, ['powerState'])
        
        logging.info("starting Server HW list loop to check server power state")
        for i, value in enumerate(server_hw_name_uri_model):
            srvr_hw_uri = server_hw_name_uri_model[i]['uri']
            srvr_hw_name = server_hw_name_uri_model[i]['name']
            srvr_hw_model = server_hw_name_uri_model[i]['model']
            power_state = srvr_hw_power_state[i]['powerState']
            if power_state == "On":
                logging.info("The server power is on. Powering off Server:  {} in {} " .format(srvr_hw_model, srvr_hw_name))
                srvr_power_check_inst.PowerOffServer(ip, auth, api, srvr_hw_uri)
                logging.info("pausing 20 secs to power off server")
                countdown(0,20)
            else:
                logging.info("Server {} in {} power is {}" .format(srvr_hw_model, srvr_hw_name, power_state))
    
    def power_on_servers(self, ip, auth, api):
        logging.info("Getting Server HW and Profiles")
        srvr_power_check_inst = CheckServerPower()
        server_hw_profiles_inst = Servers()
        server_hw_list = server_hw_profiles_inst.ServerHW(ip, auth, api)
        server_hw_name_uri_model = printDict(server_hw_list, ['name', 'uri', 'model'])
        logging.info("Getting Server Powerstate")
        srvr_hw_power_state = printDict(server_hw_list, ['powerState'])
        
        for i, value in enumerate(server_hw_name_uri_model):
            srvr_hw_uri = server_hw_name_uri_model[i]['uri']
            srvr_hw_name = server_hw_name_uri_model[i]['name']
            srvr_hw_model = server_hw_name_uri_model[i]['model']
            power_state = srvr_hw_power_state[i]['powerState']
            #logging.info("Server %s power is %s" %(srvr_hw_model, power_state))
            if power_state == "Off":
                logging.info( "The server power is off. Powering on Server:  {} in {} " .format(srvr_hw_model, srvr_hw_name))
                srvr_power_check_inst.PowerOnServer(ip, auth, api, srvr_hw_uri)
                countdown(0,30)
            elif power_state == "PoweringOn":
                logging.info("The server is powering on.  will wait 30 secs and check again")
                countdown(0,30)
                count = 0
                while True:
                    srvr_hw_power_state = printDict(server_hw_list, ['powerState'])
                    power_state = srvr_hw_power_state[i]['powerState']
                    if power_state == "PoweringOn":
                        logging.info("Server is still powering on, pausing 45 secs and will try again")
                        countdown(0,45)
                        count += 1
                        if count == 5:
                            logging.info("Something must be wrong, quiting script")
                            sys.exit(0)
                    else:
                        logging.info("Server is finally powered on, moving on")
                        break
            else:
                logging.info( "The server power is on. Moving on.")

    def check_server_power(self, ip, auth, api):
        logging.info("Getting Server HW and Profiles")
        server_hw_profiles_inst = Servers()
        server_hw_list = server_hw_profiles_inst.ServerHW(ip, auth, api)
        server_hw_name_uri_model = printDict(server_hw_list, ['name', 'uri', 'model'])
        logging.info("Getting Server Powerstate")
        srvr_hw_power_state = printDict(server_hw_list, ['powerState'])
        
        for i, value in enumerate(server_hw_name_uri_model):
            srvr_hw_name = server_hw_name_uri_model[i]['name']
            srvr_hw_model = server_hw_name_uri_model[i]['model']
            power_state = srvr_hw_power_state[i]['powerState']
            #logging.info("Server %s power is %s" %(srvr_hw_model, power_state))
            if power_state == "On":
                logging.info( "The server power is on:  {} in {} " .format(srvr_hw_model, srvr_hw_name))
            elif power_state == "PoweringOn":
                logging.info("The server is powering on.  will wait 30 secs and check again")
                countdown(0,30)
                count = 0
                while True:
                    srvr_hw_power_state = printDict(server_hw_list, ['powerState'])
                    power_state = srvr_hw_power_state[i]['powerState']
                    if power_state == "PoweringOn":
                        logging.info("Server is still powering on, pausing 45 secs and will try again")
                        countdown(0,45)
                        count += 1
                        if count == 5:
                            logging.info("Something must be wrong, quiting script")
                            sys.exit(0)
                    else:
                        logging.info("Server is finally powered on, moving on")
                        continue
            else:
                pass


class Servers(object):

    def ServerProfiles(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/server-profiles" % ip
        headers = {
            'x-api-version': api,
            'auth': auth
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
    
    def ServerProfilesTemplates(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/server-profile-templates" % ip
        headers = {
            'x-api-version': api,
            'auth': auth
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
    
    def ServerHW(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/rest/server-hardware" % ip
        headers = {
            'auth': auth,
            'x-api-version': api
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))
    
    def server_hw_firmware_inventory(self, ip, auth, api, server_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s%s/firmware" %(ip, server_uri)
        headers = {
            'auth': auth,
            'x-api-version': api
            }
        response = requests.request("GET", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(json.loads(response.text))

    def server_wwwn_wwpn(self, wwnn1_start, wwpn1_start, wwnn2_start, wwpn2_start):
        wwnn1 = [wwnn1_start+str(i) for i in range(80,100,2)]
        wwpn1 = [wwpn1_start+str(i) for i in range(80,100,2)]
        wwnn2 = [wwnn2_start+str(i) for i in range(81,100,2)]
        wwpn2 = [wwpn2_start+str(i) for i in range(81,100,2)]
        return wwnn1, wwpn1, wwnn2, wwpn2
    
    def server_profile_config_eagle3(self):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        agency = ['NASA','DEFENSE DEPT','NSA','STATE DEPT','TREASURY DEPT','CIA','COMMERCE DEPT','EDUCATION DEPT','CONGRESS','SUPREME COURT','AUSTIN','DALLAS','HOUSTON','JERUSALEM','LOS ANGELES','FRANKFURT','LONDON','MIAMI','TOKYO','SYDNEY','DENVER']
        sp_names_start = 'Server Profile '
        sp_name = [sp_names_start+str(i) for i in range(1,25,1)]
        SP_desc = 'Server Profile for '
        ServerProfilesDescriptions = [SP_desc+str(i) for i in (agency)]
        sp_descr = sorted(ServerProfilesDescriptions)
        ID1_start = ''
        id_1 = [ID1_start+str(i) for i in range(1,40,2)]
        ID2_start = ''
        id_2 = [ID2_start+str(i) for i in range(2,40,2)]
        ID3_start = ''
        id_3 = [ID3_start+str(i) for i in range(30,70,2)]
        ID4_start = ''
        id_4 = [ID4_start+str(i) for i in range(31,70,2)]
        ID5_start = ''
        id_5 = [ID5_start+str(i) for i in range(60,100,2)]
        ID6_start = ''
        id_6 = [ID6_start+str(i) for i in range(61,100,2)]
        return sp_name, sp_descr, id_1, id_2, id_3, id_4, id_5, id_6

    def server_profile_config_eagle30(self):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        agency = ['NASA','DEFENSE DEPT','NSA','STATE DEPT','TREASURY DEPT','CIA','COMMERCE DEPT','EDUCATION DEPT','CONGRESS','SUPREME COURT','AUSTIN','DALLAS','HOUSTON','JERUSALEM','LOS ANGELES','FRANKFURT','LONDON','MIAMI','TOKYO','SYDNEY','DENVER']
        sp_names_start = 'Server Profile '
        sp_name = [sp_names_start+str(i) for i in range(1,25,1)]
        SP_desc = 'Server Profile for '
        ServerProfilesDescriptions = [SP_desc+str(i) for i in (agency)]
        sp_descr = sorted(ServerProfilesDescriptions)
        ID1_start = ''
        id_1 = [ID1_start+str(i) for i in range(1,40,2)]
        ID2_start = ''
        id_2 = [ID2_start+str(i) for i in range(2,40,2)]
        ID3_start = ''
        id_3 = [ID3_start+str(i) for i in range(30,70,2)]
        ID4_start = ''
        id_4 = [ID4_start+str(i) for i in range(31,70,2)]
        ID5_start = ''
        id_5 = [ID5_start+str(i) for i in range(60,100,2)]
        ID6_start = ''
        id_6 = [ID6_start+str(i) for i in range(61,100,2)]
        ID7_start = ''
        id_7 = [ID7_start+str(i) for i in range(101,120,2)]
        return sp_name, sp_descr, id_1, id_2, id_3, id_4, id_5, id_6, id_7


    def server_profile_config(self):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        agency = ['NASA','DEFENSE DEPT','NSA','STATE DEPT','TREASURY DEPT','CIA','COMMERCE DEPT','EDUCATION DEPT','CONGRESS','SUPREME COURT']
        sp_names_start = 'Server Profile '
        sp_names_list = [sp_names_start+str(i) for i in range(1,10,1)]
        sp_names = sorted(sp_names_list)
        SP_desc = 'Server Profile for '
        ServerProfilesDescriptions = [SP_desc+str(i) for i in (agency)]
        sp_descr = sorted(ServerProfilesDescriptions)
        id1_start = ''
        id_1 = [id1_start+str(i) for i in range(1,50,2)]
        id2_start = ''
        id_2 = [id2_start+str(i) for i in range(2,50,2)]
        return sp_names, sp_descr, id_1, id_2
        
    def server_wwnn_start_wwpn_start(self, enc):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        if enc == 'Eagle155':
            array_wwpn1 = '21:70:00:c0:ff:1e:85:70'
            array_wwpn2 = '25:70:00:c0:ff:1e:85:70'
            wwnn1_start = '20:00:70:10:6F:76:B5:'
            wwpn1_start = '10:00:70:10:6F:76:B5:'
            wwnn2_start = '20:00:70:10:6F:76:B5:'
            wwpn2_start = '10:00:70:10:6F:76:B5:'
        elif enc == 'Eagle21':
            array_wwpn1 = '20:70:00:c0:ff:1e:85:70'
            array_wwpn2 = '24:70:00:c0:ff:1e:85:70'
            wwnn1_start = '20:00:70:11:6F:76:B5:'
            wwpn1_start = '10:00:70:11:6F:76:B5:'
            wwnn2_start = '20:00:70:11:6F:76:B5:'
            wwpn2_start = '10:00:70:11:6F:76:B5:'
        elif enc == 'Eagle28':
            array_wwpn1 = "21:70:00:c0:ff:25:b0:79"
            array_wwpn2 = "25:70:00:c0:ff:25:b0:79"
            wwnn1_start = '20:00:70:12:6F:76:B5:'
            wwpn1_start = '10:00:70:12:6F:76:B5:'
            wwnn2_start = '20:00:70:12:6F:76:B5:'
            wwpn2_start = '10:00:70:12:6F:76:B5:'
        elif enc == 'Eagle136':
            array_wwpn1 = '20:02:00:02:ac:01:cd:ec'
            array_wwpn2 = '21:02:00:02:ac:01:cd:ec'
            wwnn1_start = '20:00:70:13:6F:76:B5:'
            wwpn1_start = '10:00:70:13:6F:76:B5:'
            wwnn2_start = '20:00:70:13:6F:76:B5:'
            wwpn2_start = '10:00:70:13:6F:76:B5:'
        elif enc == 'Eagle20':
            array_wwpn1 = '20:70:00:c0:ff:1e:85:70'
            array_wwpn2 = '24:70:00:c0:ff:1e:85:70'
            wwnn1_start = '20:00:70:14:6F:76:B5:'
            wwpn1_start = '10:00:70:14:6F:76:B5:'
            wwnn2_start = '20:00:70:14:6F:76:B5:'
            wwpn2_start = '10:00:70:14:6F:76:B5:'
        elif enc == 'Eagle40':
            array_wwpn1 = '20:70:00:c0:ff:1e:85:70'
            array_wwpn2 = '24:70:00:c0:ff:1e:85:70'
            wwnn1_start = '20:00:70:15:6F:76:B5:'
            wwpn1_start = '10:00:70:15:6F:76:B5:'
            wwnn2_start = '20:00:70:15:6F:76:B5:'
            wwpn2_start = '10:00:70:15:6F:76:B5:'
        elif enc == 'Eagle13':
            array_wwpn1 = '20:70:00:c0:ff:1e:85:70'
            array_wwpn2 = '24:70:00:c0:ff:1e:85:70'
            wwnn1_start = '20:00:70:16:6F:76:B5:'
            wwpn1_start = '10:00:70:16:6F:76:B5:'
            wwnn2_start = '20:00:70:16:6F:76:B5:'
            wwpn2_start = '10:00:70:16:6F:76:B5:'
            
        return array_wwpn1, array_wwpn2, wwnn1_start, wwpn1_start, wwnn2_start, wwpn2_start
    
    def allocate_target_wwpn(self, icm):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        if icm == 'nitro':
            array_dict = {'Q1:1': '56:c9:ce:90:8f:75:25:01', 'Q1:2': '56:c9:ce:90:8f:75:25:0d', 'Q2:1': '56:c9:ce:90:8f:75:25:05', 'Q2:2': '56:c9:ce:90:8f:75:25:11'}
        elif icm == 'potash':
            array_dict = {'Q1:1': '56:c9:ce:90:8f:75:25:04', 'Q1:2': '56:c9:ce:90:8f:75:25:10', 'Q2:1': '56:c9:ce:90:8f:75:25:07', 'Q2:2': '56:c9:ce:90:8f:75:25:13'}
        
        for i in (array_dict):
            if i == 'Q1:1':
                port1_q1_1 = array_dict[i]
            elif i == 'Q1:2':
                port1_q1_2 = array_dict[i]
            elif i == 'Q2:1':
                port2_q2_1 = array_dict[i]
            elif i == 'Q2:2':
                port2_q2_2 = array_dict[i]
    
        return port1_q1_1, port1_q1_2, port2_q2_1, port2_q2_2


class CheckServerPower(object):

    def PowerOnServer(self, ip, auth, api, srvr_hw_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s%s/powerState" %(ip, srvr_hw_uri)
        payload = "{\r\n     \"powerState\": \"On\",\r\n     \"powerControl\":\"MomentaryPress\"\r\n}"
        headers = {
            'auth': auth,
            'x-api-version': api,
            'content-type': "application/json",
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("PUT", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
    
    def PowerOffServer(self, ip, auth ,api, srvr_hw_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s%s/powerState" %(ip, srvr_hw_uri)
        payload = "{\r\n     \"powerState\": \"Off\",\r\n     \"powerControl\":\"PressAndHold\"\r\n}"
        headers = {
            'auth': auth,
            'x-api-version': api,
            'content-type': "application/json",
            }
        logging.debug("payload: %s" % payload)
        logging.debug("url: %s" % url)
        response = requests.request("PUT", url, data=payload, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
    
    def PowerOffOnServersFunc(self, ip, auth, api):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        logging.info ("*******************POWERING OFF SERVERS ***************************")
        srvr_power_check_inst = CheckServerPower()
        logging.info("Getting Server HW and Profiles")
        server_hw_profiles_inst = Servers()
        server_hw_list = server_hw_profiles_inst.ServerHW(ip, auth, api)
        server_hw_name_uri_model = printDict(server_hw_list, ['name', 'uri', 'model'])
        logging.info("Getting Server Powerstate")
        srvr_hw_power_state = printDict(server_hw_list, ['powerState'])
        
        logging.info("starting Server HW list loop")
        for i, value in enumerate(server_hw_name_uri_model):
            srvr_hw_uri = server_hw_name_uri_model[i]['uri']
            srvr_hw_name = server_hw_name_uri_model[i]['name']
            srvr_hw_model = server_hw_name_uri_model[i]['model']
            power_state = srvr_hw_power_state[i]['powerState']
            logging.info("Server %s power is %s" %(srvr_hw_model, power_state))
            if power_state == "On":
                logging.info( "The server power is on. Powering off Server:  %s in %s " % (srvr_hw_model, srvr_hw_name))
                srvr_power_check_inst.PowerOffServer(ip, auth, api, srvr_hw_uri)
                logging.info("pausing 20 secs to power off server")
                countdown(0,20)
            else:
                pass
    
        countdown(2,0)
        logging.info ("*******************POWERING ON SERVERS ***************************")
        logging.info("Getting Server HW and Profiles")
        server_hw_profiles_inst = Servers()
        server_hw_list = server_hw_profiles_inst.ServerHW(ip, auth, api)
        server_hw_name_uri_model = printDict(server_hw_list, ['name', 'uri', 'model'])
        logging.info("Getting Server Powerstate")
        srvr_hw_power_state = printDict(server_hw_list, ['powerState'])
        
        for i, value in enumerate(server_hw_name_uri_model):
            srvr_hw_uri = server_hw_name_uri_model[i]['uri']
            srvr_hw_model = server_hw_name_uri_model[i]['model']
            power_state = srvr_hw_power_state[i]['powerState']
            logging.info("Server %s power is %s" %(srvr_hw_model, power_state))
            if power_state == "Off":
                logging.info( "The server power is off. Powering on Server:  %s in %s " % (srvr_hw_model, name))
                srvr_power_check_inst.PowerOnServer(ip, auth, api, srvr_hw_uri)
                countdown(0,30)
            else:
                pass
    
        countdown(10,0)


class DeleteEnclosureGroup(object):

    def DeleteEG(self, ip, auth, api, enc_grp_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s%s" %(ip, enc_grp_uri)
        headers = {
            'auth': auth,
            'x-api-version': api
            }
        logging.debug("url: %s" % url)    
        response = requests.request("DELETE", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)


class DeleteLogicalInterconnectGroup(object):

    def DeleteLIG(self, ip, auth, api, lig_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s%s" %(ip, lig_uri)
        headers = {
            'auth': auth,
            'x-api-version': api,
            }
        response = requests.request("DELETE", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)


class DeleteNetworks(object):

    def DeleteFcNetwork(self, ip, auth, api, network_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s/%s" % (ip, network_uri)
        headers = {
            'x-api-version': api,
            'auth': auth,
            'accept-language': "en_US"
            }
        response = requests.request("DELETE", url, headers=headers, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)
        return(response.text)


class DeleteServerProfiles(object):

    def DeleteSP(self, ip, auth, api, sp_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s%s" % (ip, sp_uri)
        querystring = {"force":"false"}
        payload = ""
        headers = {
            'x-api-version': api,
            'auth': auth
            }
        response = requests.request("DELETE", url, data=payload, headers=headers, params=querystring, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)

    def delete_sp_template(self, ip, auth, api, spt_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s%s" % (ip, spt_uri)
        querystring = {"force":"false"}
        payload = ""
        headers = {
            'x-api-version': api,
            'auth': auth
            }
        response = requests.request("DELETE", url, data=payload, headers=headers, params=querystring, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)

    def DeleteSPForce(self, ip, auth, api, sp_uri):
        logging.info("Inside function %s", sys._getframe().f_code.co_name)
        url = "https://%s%s" % (ip, sp_uri)
        querystring = {"force":"true"}
        payload = ""
        headers = {
            'x-api-version': api,
            'auth': auth
            }
        response = requests.request("DELETE", url, data=payload, headers=headers, params=querystring, verify=False)
        ValidateResponse(response.status_code, response.reason, response.text)
        logging.debug(response.text)




def get_task(ip, auth, api, task_uri):
    logging.info("Inside function %s", sys._getframe().f_code.co_name)
    url = "https://%s%s" %(ip, task_uri)
    
    headers = {
        'auth': auth,
        'x-api-version': api,
        'Content-Type': "application/json",
        }
    
    logging.debug("url: %s" % url)
    response = requests.request("GET", url, headers=headers, verify=False)
    ValidateResponse(response.status_code, response.reason, response.text)
    logging.debug(response.text)
    return(json.loads(response.text))


def GetStatusOfLogicalEnclosure(ip, auth, api):
    state = ""
    logging.info("Inside function %s", sys._getframe().f_code.co_name)
    GetLE = LogicalEnclosure()
    Resource = IsResourceDeleted()
    LeList = GetLE.GetLogicalEnclosure(ip, auth, api)
    LeState = printDict(LeList, ['state'])
    logging.info("Getting Logical Enclosure")
    LEuri = printDict(LeList, ['uri'])
    try:
        LE_uri = LEuri[0]['uri']
    except IndexError:
        print "Unable to retrieve the state of the LE\n"
        print "The LE has been deleted\n"
    try:
        state = LeState[0]['state']
    except IndexError:
        print "Unable to retrieve the state of the LE\n"
        print "The LE has been deleted\n"

    if state == "Consistent":
        logging.info ("The state of LE is consistent.  Moving on.")
        return state
    elif state == "Deleting":
        logging.info ("Looks like LE is being deleted.  Will check in 3mins to see if the LE was deleted.")
        countdown(3,0)
        count = 0
        while state == "Deleting":
            logging.info("Checking the state of the LE")
            LeList = GetLE.GetLogicalEnclosure(ip, auth, api)
            LeState = printDict(LeList, ['state'])
            try:
                state = LeState[0]['state']
            except IndexError:
                print "Unable to retrieve the state of the LE"
                print "The LE has been deleted"
                return state
            if state == "":
                logging.info("Looks like the LE has been deleted.  Moving on.")
            elif state == "Deleting":
                logging.warning("LE is still not deleted. Will check again 5 minute")
                countdown(5,0)
            count += 1
            if count == 30:
                logging.error("Something must be wrong, quiting script")
                sys.exit(0)
    elif state == "Creating":
        logging.warning("Looks like LE is being created.  Will check again in 30 secs.")
        countdown(0,30)
        count = 0
        while state == "Creating":
            logging.info("Checking the state of the LE")
            LeList = GetLE.GetLogicalEnclosure(ip, auth, api)
            LeState = printDict(LeList, ['state'])
            state = LeState[0]['state']
            if state == "Consistent":
                logging.info("The LE is in consistent state")
                continue
            elif state == "Creating":
                logging.info("Looks like the LE is still being created. Will check again 1 minute")
                countdown(1,0)
            count += 1
            if count == 25:
                logging.error("Something must be wrong, quiting script")
                sys.exit(0)
    elif state == "Inconsistent":
        logging.warning("Looks like the LE is in an inconsistent state.  Will attempt to update from group.")
        logging.info("Retrieving Logical Enclosure uri")
        LeList = GetLE.GetLogicalEnclosure(ip, auth, api)
        le_list_uri = printDict(LeList, ['uri'])
        le_uri = le_list_uri[0]['uri']
        logging.info("Updating LE from group.")
        UpdateLe = UpdateLogicalEnclosure()
        UpdateLe.LeUpdateFromGroup(ip,auth,api,le_uri)
        countdown(6,0)
        logging.info("Checking the status of the LE")
        while state == "Updating":
            logging.info("Checking the state of the LE")
            LeList = GetLE.GetLogicalEnclosure(ip, auth, api)
            LeState = printDict(LeList, ['state'])
            state = LeState[0]['state']
            if state == "Consistent":
                logging.info("The LE is in consistent state\n")
                continue
            elif state == "Updating":
                logging.warning("Looks like the LE is still being updated. Will check again 30 secs")
                countdown(0,30)
            count += 1
            if count == 25:
                logging.error("Something must be wrong, quiting script")
                sys.exit(0)
    elif state == "DeleteFailed":
        logging.error("The LE failed to get deleted")
        logging.info("Deleting the LE again using 'Force Deletion'")
        DeleteLeForce(ip,auth,api,LE_uri)
        countdown(5,0)
        logging.info("Checking if LE has been deleted")
        status = Resource.IsLeDeleted(ip, auth, api)
        print status
        if status is True:
            logging.info("LE is Deleted")
            return state
        elif status is False:
            logging.error("The LE failed to get deleted")
            logging.info("Deleting the LE again using 'Force Deletion'")
            DeleteLeForce(ip,auth,api,LE_uri)
            logging.info("Pausing 5 mins for the LE to be deleted")
            countdown(5,0)
            status = Resource.IsLeDeleted(ip, auth, api)
            print status
            if status is True:
                logging.info("LE is Deleted")
            elif status is False:
                logging.error("It seems the LE could not be deleted, quiting script\n")
                sys.exit(0)
    elif state == "Updating":
        logging.info ("\nLooks like LE is being updated.  Will check again in 1 min.")
        countdown(1,0)
        count = 0
        while state == "Updating":
            logging.info("Checking the state of the LE")
            LeList = GetLE.GetLogicalEnclosure(ip, auth, api)
            LeState = printDict(LeList, ['state'])
            state = LeState[0]['state']
            if state == "Consistent":
                logging.info("\nThe LE is in consistent state")
                return state
            elif state == "Updating":
                logging.warning("\nLooks like the LE is still being updated. Will check again 2min")
                countdown(2,0)
            count += 1
            if count == 25:
                logging.error("\nSomething must be wrong, quiting script")
                sys.exit(0)
                
    else:
        pass



def PassOrFail(result, tc):
    if result == "Pass":
        logging.testcases("%s:  PASS" %tc)
    elif result == "Fail":
        logging.testcases("%s:  FAIL" %tc)



def GetSPStatus(ip, auth, api):
    logging.info("Inside function %s", sys._getframe().f_code.co_name)
    server_hw_profiles_inst = Servers()
    ServerProfileList = server_hw_profiles_inst.ServerProfiles(ip, auth, api)
    ServerProfileUri = printDict(ServerProfileList, ['uri'])
    ServerProfileNames = printDict(ServerProfileList, ['name'])
    for sp in range(0, len(ServerProfileUri)):
        ServerProfileList = server_hw_profiles_inst.ServerProfiles(ip, auth, api)
        ServerProfileState = printDict(ServerProfileList, ['state'])
        SPstate = ServerProfileState[sp]['state']
        name = ServerProfileNames[sp]['name']
        if SPstate == "Creating":
            print ("The state of profile %s is %s\n") %(name,SPstate)
            logging.info ("Looks like Server Profiles are being created.  Will check again in 1 mins.")
            countdown(1,0)
            count = 0
            while SPstate == "Creating":
                ServerProfileList = server_hw_profiles_inst.ServerProfiles(ip, auth, api)
                ServerProfileState = printDict(ServerProfileList, ['state'])
                SPstate = ServerProfileState[sp]['state']
                if SPstate == "Normal":
                    logging.info("The server profile are in normal state")
                elif SPstate == "Creating":
                    logging.info("Looks like the server profiles are still being created. Will check again 1 minute.")
                    countdown(1,0)
                count += 1
                if count == 30:
                    logging.error("\nSomething must be wrong, quiting script\n")
                    sys.exit(0)
        elif SPstate == "Updating":
            print ("The state of profile %s is %s\n") %(name,SPstate)
            logging.info ("Looks like Server Profiles are being updated.  Will check again in 1 mins.")
            countdown(1,0)
            count = 0
            while SPstate == "Updating":
                ServerProfileList = server_hw_profiles_inst.ServerProfiles(ip, auth, api)
                ServerProfileState = printDict(ServerProfileList, ['state'])
                SPstate = ServerProfileState[sp]['state']
                if SPstate == "Normal":
                    logging.info("The server profile are in normal state")
                elif SPstate == "Updating":
                    logging.info("Looks like the server profiles are still being updated. Will check again 1 minute")
                    countdown(1,0)
                count += 1
                if count == 30:
                    logging.error("Something must be wrong, quiting script")
                    sys.exit(0)
        elif SPstate == "Deleting":
            print ("The state of profile %s is %s\n") %(name,SPstate)
            logging.info ("Looks like the server profiles are stil being deleted.  Will check in 30 secs to see if the server profiles have been deleted.")
            countdown(0,30)
            count = 0
            while SPstate == "Deleting":
                ServerProfileList = server_hw_profiles_inst.ServerProfiles(ip, auth, api)
                ServerProfileState = printDict(ServerProfileList, ['state'])
                try:
                    SPstate = ServerProfileState[sp]['state']
                except IndexError as e:
                    logging.info (e)
                if SPstate == "Deleting":
                    logging.info("Server profiles have still not deleted. Will check again 3 minute")
                    print count
                    countdown(3,0)
                    Resource = IsResourceDeleted()
                    status = Resource.IsSPDeleted(ip, auth, api)
                    print status
                    if status == True:
                        logging.info("Server Profiles have been Deleted")
                        #return status
                        break
                    elif status == False:
                        logging.info("Server Profiles have not been deleted")
                else:
                    pass
                count += 1
                if count == 30:
                    logging.error("Something must be wrong, quiting script")
                    sys.exit(0)
        elif SPstate == "DeleteFailed":
            logging.error("One or more server profiles failed to delete, quiting script")
            sys.exit(0)
        elif SPstate == "CreateFailed":
            logging.error("One or more server profiles failed to create.")
        elif SPstate == "Normal":
            logging.info("The state of server profile %s is %s\n" %(name,SPstate))
            
    try:
        return SPstate
    except UnboundLocalError:
        print "No server profiles"


def GetSPTStatus(ip, auth, api):
    logging.info("Inside function %s", sys._getframe().f_code.co_name)
    server_hw_profile_template_instance = Servers()
    server_profile_template_list = server_hw_profile_template_instance.ServerProfilesTemplates(ip, auth, api)
    server_profile_template_uri = printDict(server_profile_template_list, ['uri'])
    ServerProfileNames = printDict(server_profile_template_list, ['name'])
    for spt in range(0, len(server_profile_template_uri)):
        server_profile_template_list = server_hw_profile_template_instance.ServerProfilesTemplates(ip, auth, api)
        server_profile_template_state = printDict(server_profile_template_list, ['state'])
        SPT_state = server_profile_template_state[spt]['state']
        spt_name = ServerProfileNames[spt]['name']
        if SPT_state == "Creating":
            print ("The state of profile template %s is %s\n") %(spt_name,SPT_state)
            logging.info ("Looks like Server Profiles are being created.  Will check again in 1 mins.")
            countdown(1,0)
            count = 0
            while SPT_state == "Creating":
                server_profile_template_list = server_hw_profile_template_instance.ServerProfilesTemplates(ip, auth, api)
                server_profile_template_state = printDict(server_profile_template_list, ['state'])
                SPT_state = server_profile_template_state[spt]['state']
                if SPT_state == "Normal":
                    logging.info("The server profile template are in normal state")
                elif SPT_state == "Creating":
                    logging.info("Looks like the server profile templates are still being created. Will check again 1 minute.")
                    countdown(1,0)
                count += 1
                if count == 30:
                    logging.error("\nSomething must be wrong, quiting script\n")
                    sys.exit(0)
        elif SPT_state == "Updating":
            print ("The state of profile template %s is %s\n") %(spt_name,SPT_state)
            logging.info ("Looks like Server Profiles are being updated.  Will check again in 1 mins.")
            countdown(1,0)
            count = 0
            while SPT_state == "Updating":
                server_profile_template_list = server_hw_profile_template_instance.ServerProfilesTemplates(ip, auth, api)
                server_profile_template_state = printDict(server_profile_template_list, ['state'])
                SPT_state = server_profile_template_state[spt]['state']
                if SPT_state == "Normal":
                    logging.info("The server profile template are in normal state")
                elif SPT_state == "Updating":
                    logging.info("Looks like the server profile templates are still being updated. Will check again 1 minute")
                    countdown(1,0)
                count += 1
                if count == 30:
                    logging.error("Something must be wrong, quiting script")
                    sys.exit(0)
        elif SPT_state == "Deleting":
            print ("The state of profile template %s is %s\n") %(spt_name,SPT_state)
            logging.info ("Looks like the server profile templates are stil being deleted.  Will check in 30 secs to see if the server profile templates have been deleted.")
            countdown(0,30)
            count = 0
            while SPT_state == "Deleting":
                server_profile_template_list = server_hw_profile_template_instance.ServerProfilesTemplates(ip, auth, api)
                server_profile_template_state = printDict(server_profile_template_list, ['state'])
                try:
                    SPT_state = server_profile_template_state[spt]['state']
                except IndexError as e:
                    logging.info (e)
                if SPT_state == "Deleting":
                    logging.info("Server profile templates have still not deleted. Will check again 3 minute")
                    print count
                    countdown(3,0)
                    Resource = IsResourceDeleted()
                    status = Resource.IsSPDeleted(ip, auth, api)
                    print status
                    if status == True:
                        logging.info("Server Profiles have been Deleted")
                        #return status
                        break
                    elif status == False:
                        logging.info("Server Profiles have not been deleted")
                else:
                    pass
                count += 1
                if count == 30:
                    logging.error("Something must be wrong, quiting script")
                    sys.exit(0)
        elif SPT_state == "DeleteFailed":
            logging.error("One or more server profile templates failed to delete, quiting script")
            sys.exit(0)
        elif SPT_state == "CreateFailed":
            logging.error("One or more server profile templates failed to create.")
        elif SPT_state == "Normal":
            logging.info("The state of server profile template %s is %s\n" %(spt_name,SPT_state))
            
    try:
        return SPT_state
    except UnboundLocalError:
        print "No server profile templates"


def create_log_file(filename, level=logging.DEBUG):
    TimeStamp = time.strftime("%Y%m%d_%H%M%S")
    handler = logging.FileHandler(filename)
    handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    handler.setFormatter(formatter)
    logging.getLogger('').addHandler(handler)


def setup_logging_Enhanced(enc, file):
    #Set up logging
    #components = ('_' + enc + '_' + version + '_' + carbon_fw)
    components = ('_' + enc + '_' + file)
    logging.getLogger('').setLevel(logging.DEBUG)
    TimeStamp = time.strftime("%Y%m%d_%H%M%S")
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    #open up a few files for logging at different levels
    create_log_file('logs/' + TimeStamp + components + '_DEBUG.log', logging.DEBUG)
    create_log_file('logs/' + TimeStamp + components + '_INFO.log', logging.INFO)
    create_log_file('logs/' + TimeStamp + components + '_WARNING.log', logging.WARNING)
    create_log_file('logs/' + TimeStamp + components + '_ERROR.log', logging.ERROR)
    #create_log_file('logs/' + TimeStamp + components + '_CRITICAL.log', logging.CRITICAL)
    create_log_file('logs/' + TimeStamp + components + '_TESTCASES.log', logging.TESTCASES)
    #logging.basicConfig() 
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

def printDict(myDict, keys):
    myDictList = []
    myValues = []
    for x in range(0, len(myDict['members'])):
        for key in keys:
            myValues.append(myDict['members'][x][key])
        myDictList.append(dict(zip(keys, myValues)))
        myValues = []
    return(myDictList)

def countdown(p,q):
    i=p
    j=q
    k=0
    while True:
        if(j==-1):
            j=59
            i -=1
        if(j > 9):  
            print "\r"+str(k)+str(i)+":"+str(j),
        else:
            print "\r"+str(k)+str(i)+":"+str(k)+str(j),
        time.sleep(1)
        j -= 1
        if(i==0 and j==-1):
            break
    if(i==0 and j==-1):
        print "\rContinuing!"
        time.sleep(1)
# example: countdown(5,5) #countdown(min,sec)


def get_eagle_enclosure_map(ip):
    #ip to eagle name map
    eagle_to_enclosure_dict = {
        '15.186.9.20': 'Eagle20',
        '15.186.9.21': 'Eagle21',
        '15.186.9.28': 'Eagle28',
        '15.186.9.30': 'Eagle30',
        '15.186.9.31': 'Eagle31',
        '15.186.9.32': 'Eagle32',
        '15.186.9.40': 'Eagle40',
        '15.186.9.76': 'Eagle76',
        '15.186.9.77': 'Eagle77',
        '15.186.9.78': 'Eagle78',
        '15.186.9.13': 'Eagle13',
        '15.186.9.14': 'Eagle14',
        '15.186.9.86': 'Eagle86',
        '15.186.9.136': 'Eagle136',
        '15.186.9.50': 'Eagle50',
        '15.186.9.35': 'Eagle35',
        '15.186.9.119': 'Eagle119',
        '15.186.9.3': 'Eagle3',
        '15.186.9.152': 'Eagle152',
        '15.186.9.155': 'Eagle155',
        '15.186.9.11': 'Eagle11',
        '15.186.9.157': 'Eagle157',
        '15.186.9.123': 'Eagle123',
        '15.186.9.159': 'Eagle159',
        '15.186.9.131': 'Eagle131',
        '15.186.9.146': 'Eagle146',
        '15.245.131.222': 'Nitro_Potash_mix_OVF9549',
        '15.186.9.71': 'Eagle71'
        }
    if ip in eagle_to_enclosure_dict:
        eagle = eagle_to_enclosure_dict[ip]
    elif ip not in eagle_to_enclosure_dict:
        eagle = 'DefaultEagle'
    else:
        print "You need to specify ip address or update eagle_enclosure map function with new ip address"
        sys.exit(0)
    return eagle






















def ValidateResponse(status_code, reason, text):
    logging.info("Inside function %s", sys._getframe().f_code.co_name)
    logging.debug("status_code = %i: OK", status_code)
    if status_code > 299:
        logging.debug("status_code > 299")
        if status_code == 400:
            print
            logging.warning("%i: %s", status_code, reason)
            logging.warning(text)
            if text.find('Please retry this operation later.', 0) > 0:
                logging.warning("Sleeping for 30 seconds to allow OneView time to catch up!")
                countdown(1,0)
                return False
            logging.warning("Non fatal error, continuing...")
            time.sleep(3)
        else:  
            logging.error("%i: %s", status_code, reason)
            logging.error(text)
            logging.error("Exiting...")
            exit(1)
    return True

def sshclient(ip, user, cim_pw, cmd):
    logging.info("Inside function %s", sys._getframe().f_code.co_name)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username = user, password= cim_pw, port=22)

    (stdin, stdout, stderr) = ssh.exec_command(cmd)
    
    output = stdout.read()
    #logging.debug(output)
    ssh.close()
    return output




















