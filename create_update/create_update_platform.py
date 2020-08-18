#!/usr/bin/python3

import requests, json, hashlib, os, sys
import connect_platform as platform

class Firmware:
	def __init__(self, file, md5_file, version):
		self.file = file
		self.md5_file = md5_file
		self.version = version
		
	def print_fw(self):
		print("==========================================")
		print("File:\t\t", self.file)
		print("Chacksum:\t", self.md5_file)
		print("Version:\t", self.version)
		print("==========================================")
		
	def get_files_content(self):
		f = open(self.file, 'rb')
		if(os.path.isfile(self.md5_file)):
			md5sum = open(self.md5_file, 'rb')
		else:
			md5sum = hashlib.md5(f.read()).hexdigest()
		return f, md5sum

################################# End of class Firmware ############################################

class DeviceInfo:
	def __init__(self, name, guid, dev_id):
		self.name = name
		self.guid = guid
		self.dev_id = dev_id
		
	def set_status(self, status):
		self.status = status
		
	def set_version(self, version):
		self.version = version
		
	def set_upload_info(self, data):
		self.upload_info = data

################################# End of class DeviceInfo ############################################

class Device(Firmware, DeviceInfo):
	def __init__(self, name, guid, dev_id, file, md5sum, version):
		Firmware.__init__(self, file, md5sum, version)
		DeviceInfo.__init__(self, name, guid, dev_id)
		
	def get_fw_info(self):
		return Firmware(self.file, self.md5_file, self.version)

################################# End of class Device ############################################

def create_fw_req(plat, header, fw):
	file, md5sum = fw.get_files_content()
	multipart_form_data = {'firmware': file, 'checksum': md5sum}
	fw.print_fw();
	
	print("Sending...")
	r = requests.request('POST', url="{}/{}/firmwares/{}".format(plat.api, plat.params['application'], plat.params['deviceModelName']), headers=header, params={'version': fw.version}, files=multipart_form_data)
	
	return r

def create_update_req(plat, header, device):
	data = {"deviceGuid": device.guid, "status": "PENDING", "version": device.version}
#	json_body = json.dumps(data)
	
	print(">> Headers: ", header)
	print(">> Body: ", json.dumps(data))
	
	print("Sending...")
	r = requests.request('POST', url="{}/{}/firmwareupdates/".format(plat.api, plat.params['application']), headers=header, json=data)
	print("PreparedRequest => ", r.request.path_url, r.request.body)
	
	return r

def request(req_type, plat, header, device):
	# Send request
	print("Creating {} request".format(req_type))

	if req_type == 'fw':
		r = create_fw_req(plat, header, device.get_fw_info())
	else:
		r = create_update_req(plat, header, device)

#	print("Return header ", r.headers)
	print("Endpoint ", r.url)
	print("Status: ", r.status_code, r.reason)

	# Extract data from response in json format
	data = r.json()

	print("Data returned:")
	print(json.dumps(data, indent=4))
	
	return r.status_code, data
	
# Entire process to create an update
def new_fw(plat, device):
	print("Creating update for device", device.name)
	r, data = request('fw', plat, plat.header, device)
	if (r != 200) and (data['status'] != 'success'):
		print("Failed to create update for device ", device.name)
		return False
	device.set_upload_info(data['result'])
	header = {"Content-Type": "application/json"}
	header.update(plat.header)
#	header['Authorization'] = header['Authorization'].format(token['access_token'])
	r, data = request('update', plat, header, device)
	if (r != 200) and (data['status'] != 'success'):
		print("Failed to create update for device ", device.name)
		return False
		
	return True

def create_updates(plat, devices):
	ok = True
	for d in devices:
		ok = ok and new_fw(plat, d)
	
	return ok

def main(argv):
	p = platform.Platform(user = "mjuliabs@gmail.com", pwd = "123456", api="http://192.168.0.123:8081/v1")
	devices = []
	dev_id = 'node02'
	dev_guid = '194648e0-c554-4353-bc41-dc8a670c19b9'
	dev_name = 'nodeMCU 02'
	fwbin_file = 'C:/Users/majubs/Documents/Unicamp/Konker/libKonkerESP/.pio/build/nodemcuv2/firmware.bin'
	md5_file = 'C:/Users/majubs/Documents/Unicamp/Konker/libKonkerESP/.pio/build/nodemcuv2/checksum.txt'
	v = '1.0.6'
	devices.append(Device(dev_name, dev_guid, dev_id, fwbin_file, md5_file, v))
	
	ok = create_updates(p, devices)
	if ok:
		print("Updates created.")
	else:
		print("It was not possible to create update for all devices!")
#		return

if __name__ == "__main__":
	main(sys.argv)