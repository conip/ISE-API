#!/usr/bin/python3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
import json
import ipaddress
import urllib
import sys
import getopt
#import urllib2
from tabulate import tabulate
#---------------------------------------------------------------------------------------------------------------
def get_sgt_value(sgtid):
    url = url_builder(ssl, server, port, '/ers/config/sgt/' + sgtid)
    method = "GET"
    headers = {'Accept':'application/json',
               'Content-Type':'application/json;charset=utf-8'}
    
    try:
        con = open_url(url, headers=headers, method=method, use_proxy=False, force_basic_auth=True,
                   validate_certs=validate_certs,  url_username=username, url_password=password)    
        
        result_con = json.loads(con.read())
        var_sgt_number = result_con['Sgt']['value'] 
        return var_sgt_number
    except: 
        return "unknown"
#---------------------------------------------------------------------------------------------------------------
def get_all_sgt_list_json():
    page = 1
    result = {}
    var_id_tmp = ''
    while _get_all_sgt_list_json(page, result):
        page += 1
    return result
#---------------------------------------------------------------------------------------------------------------
def _get_all_sgt_list_json(page, result):
    url = url_builder(ssl, server, port, '/ers/config/sgt?size=100&page=' + str(page))
    method = "GET"
    headers = {'Accept':'application/json',
               'Content-Type':'application/json;charset=utf-8'}
    con = open_url(url, headers=headers, method=method, use_proxy=False, force_basic_auth=True,
                   validate_certs=validate_certs,  url_username=username, url_password=password)
    if con.code == 200:
        result_con_all = json.loads(con.read())
        result_total = result_con_all['SearchResult']['total']
        last = False
        for i, value in enumerate(result_con_all['SearchResult']['resources']):
            result[value['name']] = {
                "id": value['id'],
                "sgt_value" : get_sgt_value(value['id'])}
 
            #print(value['name'] + '\t\t\t\t\t\t ---> ' + "SGT = " + str(var_tmp))
        if (page * 100) >= result_total:
            last = True
        if not last:
            return True
    return False
#--------------------------------------------------------------------------------------------------------------
def add_ip_to_sgt_mapping(var_dev_IP, var_dev_NAME, var_tag_id):
    body = '{"SGMapping":{"name":"' + var_dev_NAME + '","sgt":"' + var_tag_id + '","deployType": "ALL","hostIp": "' + var_dev_IP + '/32"} }'
    
    # should be similar to this
    #
    # sgt_body = {
    #     "SGMapping" : {
    #         "name" : "testsrv3",
    #         "sgt": "cacbda50-d51c-11eb-a79c-ba77bddd2f05",
    #         "deployType": "ALL",
    #         "hostIp": "11.11.11.103/32"
    #     }
    # }
    url = url_builder(ssl, server, port, ISE_URL)
    method = "POST"
    headers = {'Accept':'application/json',
               'Content-Type':'application/json;charset=utf-8'}
    #print(body)
    try: 
        con = open_url(url, data=body, headers=headers, method=method, use_proxy=False, force_basic_auth=True,
                   validate_certs=validate_certs,  url_username=username, url_password=password)
    except:
        print(" --- "+ var_dev_NAME + " : " + var_dev_IP+  "\t\t FAILED")
        return False
    if con.code == 201:
        print(" --- "+ var_dev_NAME + " : " + var_dev_IP + "\t\t OK")
        return True
    print(" --- "+ var_dev_NAME + " : " + var_dev_IP+  "\t\t FAILED")
    return False
#--------------------------------------------------------------------------------------------------------------
def url_builder(ssl, server, port, extension):
    protocol = "https" if ssl else "http"
    return protocol + "://" + server + ":" + port + extension
#---------------------------------------------------------------------------------------------------------------
def main(argv):
    global ssl, username, password, validate_certs, server, port, force, ISE_URL
    server = port = username = password = ""
    ssl = validate_certs = force = False
    ISE_URL = '/ers/config/sgmapping'
    server = '192.168.101.100'
    port = '9060'
    username = 'ansible_ise'
    password = 'Alamakota$123'
    ssl = True
    var_sgt_name = ''
    var_sgt_value = ''
    var_sgt_id = ''
    var_list = False
    var_column_headers = ['SGT NAME:',"SGT VALUE:"]
    try:
        var_cli_opts, var_cli_args = getopt.getopt(argv, "hln:v:",["help","list","sgt_name=","sgt_value="])
    except getopt.GetoptError:
        print("Missing one of the option")
        sys.exit(2)
    
    for var_opt, var_arg in var_cli_opts:
        if var_opt == "-h":
            print("\nUse one of the following:")
            print("---------------------------------------")
            print("python ip_sgt_mapping.py -n [sgt_name]")
            print("python ip_sgt_mapping.py -v [sgt_value]")
            print("\nTo list all defined SGTs in ISE use:")
            print("---------------------------------------\npython ip_sgt_mapping.py -l")
            sys.exit()
        if var_opt in ("-n", "--sgt_name"):
            var_sgt_name = var_arg
        if var_opt in ("-v", "--sgt_value"):
            var_sgt_value = var_arg
        if var_opt == "-l":
            var_list = True
    
    var_all_sgt_list = get_all_sgt_list_json()    
    if (var_sgt_value == '' and var_sgt_name == '') or var_list == True:
        table = []
        print("\nLIST of all SGT defined:")
        for key,value in var_all_sgt_list.items():
            table.append((str(key),str(value['sgt_value'])))
        print(tabulate(table, var_column_headers))
        sys.exit()
    
    if var_sgt_name != '':
        if var_sgt_name not in var_all_sgt_list.keys():
            print("NO SUCH TAG DEFINED ON ISE!")
            sys.exit()
        var_sgt_id = var_all_sgt_list[var_sgt_name]['id']
    
    if var_sgt_value != '':
        for item_key, item_value in var_all_sgt_list.items():
            #print("item_value = "+str(item_value['sgt_value']) + " --- var_sgt_value= " + str(var_sgt_value))
            if str(item_value['sgt_value']) == str(var_sgt_value):
                var_sgt_id = var_all_sgt_list[item_key]['id']
    with open('Sheet1.json') as json_file:
        file_data = json.load(json_file)
    #print(json.dumps(data))
    #print(var_sgt_id)
    #print(var_all_sgt_list)
    # list_dev = [
    #     {
    #         "IP Address" : "22.22.22.104",
    #         "Device Name": "dev104"
    #     },
    #     {
    #         "IP Address" : "22.22.22.106",
    #         "Device Name": "dev106"            
    #     }
    # ]
    for single_device_dict in file_data:
        device_IP = single_device_dict["IP Address"]
        device_NAME = single_device_dict["Server Name"]
        add_ip_to_sgt_mapping(device_IP, device_NAME, var_sgt_id)
    #device_IP = '22.22.22.103'
    #device_NAME = 'srvtest3'    
    #add_ip_to_sgt_mapping(device_IP, device_NAME, var_sgt_id)
#------------------------------------------------------- MAIN EXECUTION --------------------------------------------------    
if __name__ == '__main__':
    main(sys.argv[1:])
