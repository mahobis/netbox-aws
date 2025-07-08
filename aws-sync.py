import json
import boto3
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Connect to AWS EC2 API
ec2 = boto3.client('ec2', verify=False)

# Retrieve information about instances
instances = ec2.describe_instances()

# Use NetBox API to retrieve list of device types
url = 'https://netbox.lan/api/dcim/device-types/'
token = ''
headers = {'Authorization': 'Token {}'.format(token), 'Content-Type': 'application/json'}

device_types_response = requests.get(url, headers=headers, verify=False)
device_types = device_types_response.json()['results']

# Extract information about instances
for reservation in instances['Reservations']:
    for instance in reservation['Instances']:
        vcpus = 0
        local_ip = instance['PrivateIpAddress']
        #public_ip = instance['PublicIpAddress']
        public_ip = instance.get("PublicIpAddress")
       #hostname = instance['InstanceId']
        instance_name = None
        for tag in instance['Tags']:
            if tag['Key'] == 'Name':
                instance_name = tag['Value']
                break
        if instance_name is None:
            instance_name = instance['InstanceId']
        hostname = instance_name
        region = instance['Placement']['AvailabilityZone']
        description = instance['InstanceType']
        tags = [{'id': 1}]
        comments = instance['InstanceId']
        instance_id = instance['InstanceId']
        instance_type_name = instance['InstanceType']
        instance_type = ec2.describe_instance_types(InstanceTypes=[instance_type_name])
        current_vcpu_count = instance_type['InstanceTypes'][0]['VCpuInfo']['DefaultVCpus']
        vcpus += current_vcpu_count
        status = instance['State']['Name']
        memory = instance_type['InstanceTypes'][0]['MemoryInfo']['SizeInMiB']
        # Get details of each disk
#        disks = []
        for block_device_mapping in instance['BlockDeviceMappings']:
            volume_id = block_device_mapping['Ebs']['VolumeId']
            volume = ec2.describe_volumes(VolumeIds=[volume_id])
            disk_size = volume['Volumes'][0]['Size']

        if 'stopped' in status:
            status = "offline"
        else:
            status = "active"


        # Find the ID of the device type that matches the instance type
        device_type_id = 4
        for device_type in device_types:
            if device_type['model'] == description:
                device_type_id = device_type['id']
                break
        device_role = 2
        site = 2

        # Use NetBox API to check if virtual machine with this name already exists
        url = 'https://netbox.lan/api/virtualization/virtual-machines/?name={}'.format(hostname)
        response = requests.get(url, headers=headers, verify=False)
        virtual_machine = response.json()['results']

        if virtual_machine:
            # Virtual machine exists, update it with the information from AWS EC2
            virtual_machine_id = virtual_machine[0]['id']
            url = 'https://netbox.lan/api/virtualization/virtual-machines/{}/'.format(virtual_machine_id)
#            data = {'status':status,'name': hostname,'site': site, 'tags': tags , 'device_role': device_role, 'device_type': device_type_id, 'region': region,'description': description, 'comments': comments,'vcpus': vcpus}
            data = {'status':status,'name': hostname,'site': site, 'tags': tags , 'device_role': device_role, 'device_type': device_type_id, 'region': region, 'description': description, 'comments': comments, 'vcpus': vcpus, 'memory': memory, 'disk_name': volume_id, 'disk_size': disk_size}

            response = requests.patch(url, headers=headers, json=data, verify=False)

            if response.status_code == 200:
                print('Virtual machine updated in NetBox successfully.')
            else:
                print('Error updating virtual machine in NetBox: {}'.format(response.text))
        else:
            # Virtual machine does not exist, create it in NetBox
            url = 'https://netbox.lan/api/virtualization/virtual-machines/'
            data = {'status':status,'name': hostname,'site': site, 'tags': tags , 'device_role': device_role, 'device_type': device_type_id, 'region': region, 'description': description, 'comments':comments, 'vcpus': vcpus, 'memory': memory, 'disk_name': volume_id, 'disk_size': disk_size}

            response = requests.post(url, headers=headers, json=data, verify=False)

### Creating private and public interface for vm in netbox


        print(public_ip)

        url = 'https://netbox.lan/api/virtualization/interfaces/?virtual_machine={}'.format(hostname)
        response = requests.get(url, headers=headers, verify=False)
        print(response.json()['results'])
        virtual_machine11 = response.json()['results']


        if virtual_machine11:
            virtual_machine_id = virtual_machine11[0]['id']

            url = 'https://netbox.lan/api/virtualization/interfaces/'
            ip_data = [{'id':virtual_machine_id,'name':hostname,'virtual_machine':{'name':hostname}, 'display':"local-ip",'enabled': "true" }]
            ip_response = requests.patch(url, headers=headers, json=ip_data, verify=False)
            str1 = hostname
            str2 = " PublicIP"
            publichostname = " ".join((str1, str2))
            url = 'https://netbox.lan/api/virtualization/interfaces/'
            ip_data = [{'name':publichostname,'virtual_machine':{'name':hostname},'display':"public-ip", 'enabled': "true" }]
            ip_response = requests.patch(url, headers=headers, json=ip_data, verify=False)

            if ip_response.status_code == 200:
                print('Interface updated in NetBox successfully.')
            else:
                print('Error Interface updated  in NetBox: {}'.format(ip_response.text))

        else:
                # Add IP address to virtual machine
                str1 = hostname
                str2 = " PublicIP"
                publichostname = " ".join((str1, str2))

                url = 'https://netbox.lan/api/virtualization/interfaces/'
                ip_data = {'name':hostname, 'virtual_machine':{'name':hostname},'display':"local-ip", 'enabled': "true", }
                ip_response = requests.post(url, headers=headers, json=ip_data, verify=False)

                url = 'https://netbox.lan/api/virtualization/interfaces/'
                ip_data = {'name':publichostname, 'virtual_machine':{'name':hostname},'display':"public-ip", 'enabled': "true", }
                ip_response = requests.post(url, headers=headers, json=ip_data, verify=False)




#### Creating local ip address


        url = 'https://netbox.lan/api/ipam/ip-addresses/?address={}'.format(local_ip)
        response = requests.get(url, headers=headers, verify=False)
        virtual_machine1 = response.json()['results']


        if virtual_machine1:
            virtual_machine_id = virtual_machine1[0]['id']

            url5 = 'https://netbox.lan/api/virtualization/interfaces/?name={}'.format(hostname)
            response5 = requests.get(url5, headers=headers, verify=False)
            virtual_machine5 = response5.json()['results']

            interface_id = 0
            interface_id = virtual_machine5[0]['id']
            url = 'https://netbox.lan/api/ipam/ip-addresses/'
#            ip_data = {'address': local_ip ,'assigned_object_type': "virtualization.vminterface"}
#            ip_data = [{'id':interface_id,'address': local_ip ,'assigned_object_type': None,'assigned_object_id': None , 'vrf:':14}]
            ip_data = [{'id':interface_id,'address': local_ip}]
#            ip_data = [{'id':interface_id ,'status':"active",'address': local_ip , 'vrf':14, 'device': hostname,'virtual_machine': hostname, 'interface': hostname,'is_primary':"true"}]

            ip_response = requests.patch(url, headers=headers, json=ip_data, verify=False)

            if ip_response.status_code == 200:
                print('Private ip adress  updated in NetBox successfully.')
            else:
                print('Error updating private ip adress in NetBox: {}'.format(ip_response.text))

        else:
                # Add IP address to virtual machine
                url5 = 'https://netbox.lan/api/virtualization/interfaces/?name={}'.format(hostname)
                response5 = requests.get(url5, headers=headers, verify=False)
                virtual_machine5 = response5.json()['results']

                interface_id = 0
                interface_id = virtual_machine5[0]['id']

                url = 'https://netbox.lan/api/ipam/ip-addresses/'
            #    ip_data = {'address': local_ip }
                ip_data = {'id':interface_id,'address': local_ip ,'assigned_object_type': 'virtualization.vminterface','assigned_object_id': interface_id }
                ip_response = requests.post(url, headers=headers, json=ip_data, verify=False)


                if public_ip:
                    str1 = hostname
                    str2 = " PublicIP"
                    publichostname = " ".join((str1, str2))
                    url5 = 'https://netbox.lan/api/virtualization/interfaces/?name={}'.format(publichostname)
                    response5 = requests.get(url5, headers=headers, verify=False)
                    virtual_machine5 = response5.json()['results']

                    interface_id = 0
                    interface_id = virtual_machine5[0]['id']

                    url = 'https://netbox.lan/api/ipam/ip-addresses/'
            #    ip_data = {'address': local_ip }
                    ip_data = {'id':interface_id,'address': public_ip ,'assigned_object_type': 'virtualization.vminterface','assigned_object_id': interface_id }
                    ip_response = requests.post(url, headers=headers, json=ip_data, verify=False)
