""" Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. 
"""

"""
Script Dependencies:
    suds
Depencency Installation:
    $ pip install suds-py3
"""

import pathlib
import ssl
from suds.client import Client
from suds.xsd.doctor import Import
from suds.xsd.doctor import ImportDoctor

import os
import sys
from suds.client import Client
from suds.transport.https import HttpAuthenticated
from suds.xsd.doctor import ImportDoctor, Import
from urllib.request import HTTPSHandler
import urllib.error
import urllib.request
import ssl
import user_env
from bs4 import BeautifulSoup

global mac


# function for api AXL request
def axl_request():
    phone_list = []

    # Disable HTTPS certificate validation check - not recommended for production
    if hasattr(ssl, "_create_unverified_context"):
        ssl._create_default_https_context = ssl._create_unverified_context

    tns = "http://schemas.cisco.com/ast/soap/"
    imp = Import("http://schemas.xmlsoap.org/soap/encoding/")
    imp.filter.add(tns)

    # adding the ip address provided onto the url link for the API call
    url = "https://" + user_env.CUCM_LOCATION + "/axl/"

    # connecting to CUCM device using axl
    axl = Client(
        "file:" + os.getcwd() + "/app/schema/AXLAPI.wsdl",
        location=url,
        faults=False,
        plugins=[ImportDoctor(imp)],
        username=user_env.CUCM_USER,
        password=user_env.CUCM_PASSWORD,
    )

    list_of_devices = []

    # axl api call being made and filter name with any devices that start with SEP (all phones)
    # refer to AXL documentation to see the more phone info you can receive with returnedTags

    res = axl.service.listPhone(
        {"name": "SEP%"},
        returnedTags={
            "name": "",
            "description": "",
            "model": "",
            "networkLocation": "",
            "product": "",
            "class": "",
            "protocol": "",
            "protocolSide": "",
            "callingSearchSpaceName": "",
            "devicePoolName": "",
            "commonDeviceConfigName": "",
            "commonPhoneConfigName": "",
            "networkLocation": "",
            "locationName": "",
        },
    )

    # verifying if the response was successful
    if res[0] == 200:
        if res[1]["return"]:
            phones = res[1]["return"]["phone"]

            for phone in list(phones):
                phone_list.append(phone)
    else:
        ("Response Error from AXL API Call")

    return phone_list


# function for api risport request
def risport_request():
    phone_list = []

    # Disable HTTPS certificate validation check - not recommended for production
    if hasattr(ssl, "_create_unverified_context"):
        ssl._create_default_https_context = ssl._create_unverified_context

    url = (
        "https://"
        + user_env.CUCM_LOCATION
        + ":8443/realtimeservice/services/RisPort?wsdl"
    )

    tns = "http://schemas.cisco.com/ast/soap/"
    imp = Import(
        "http://schemas.xmlsoap.org/soap/encoding/",
        "http://schemas.xmlsoap.org/soap/encoding/",
    )
    imp.filter.add(tns)

    t = HttpAuthenticated(username=user_env.CUCM_USER, password=user_env.CUCM_PASSWORD)
    t.handler = urllib.request.HTTPBasicAuthHandler(t.pm)

    context = ssl.SSLContext()

    t1 = urllib.request.HTTPSHandler(context=context)
    t.urlopener = urllib.request.build_opener(t.handler, t1)

    c = Client(url, plugins=[ImportDoctor(imp)], transport=t)

    result = c.service.SelectCmDevice(
        "", {"SelectBy": "Name", "Status": "Any", "Class": "Phone"}
    )

    total_phones = result["SelectCmDeviceResult"]["TotalDevicesFound"]

    list_phones = result["SelectCmDeviceResult"]["CmNodes"]

    for node in result["SelectCmDeviceResult"]["CmNodes"]:
        for device in node["CmDevices"]:
            phone_list.append(device)

    return phone_list


# function to extract serial number from the phone's web page
def get_scraped_phone_data(ip_address):
    url = "http://" + ip_address
    try:
        fhand = urllib.request.urlopen(url).read()
    except:
        print("unable to reach site")
        return "unaccessible"

    soup = BeautifulSoup(fhand, "html.parser")
    phoneData = soup.find_all("b")

    searchList = ["mac address", "serial number", "model number", "hardware revision"]
    mac = serial_num = hw_r = model_number = ""
    for bTag in range(len(phoneData)):
        bText = phoneData[bTag].text.strip().lstrip().lower()
        if bText in searchList:
            if bText == "hardware revision":
                hw_r = phoneData[bTag + 1].text
            elif bText == "serial number":
                serial_num = phoneData[bTag + 1].text
            elif bText == "model number":
                model_number = phoneData[bTag + 1].text
            elif bText == "mac address":
                mac = phoneData[bTag + 1].text
            # else:
            #   d = [mac, serial_num, hw_r]
            #   return d
    d = [mac, serial_num, hw_r, model_number]
    return d


# axl_request()
# risport_request()
# get_scraped_phone_data
