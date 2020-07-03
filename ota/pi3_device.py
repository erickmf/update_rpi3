#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 18:50:59 2020

@author: majubs
"""
import json, requests, os, platform, subprocess, psutil
from zipfile import ZipFile
from time import time

class Device:
	# load device information for checks later
	def __init__(self, user, passwd, fw_info_file="fw_info.json"):
		try:
			with open(fw_info_file, 'r') as f:
				content = json.loads(f.read())
			print("Device information: ")
			print(json.dumps(content, indent=4))
                
			if content.get("version"):
				self.version = content["version"]
			else:
				self.version = '0.0.0'
			if content.get("device"):
				self.device = content["device"]
			else:
				self.device = 'node00'
			if content.get("sequence_number"):
				self.sequence_number = content["sequence_number"]
			else:
				self.sequence_number = '9999999999999'
			if content.get("backup"):
				self.backup_file = content["backup"]
			else:
				self.backup_file = "fw.zip"
		except:
			self.version = '0.0.0'
			self.device = 'node00'
			self.sequence_number = '9999999999999'
			self.backup_file = "fw.zip"
# 		self.directory_list = ['conf', 'rtd-LoRa', 'master'] #, 'ota']
		self.directory_list = ['app']
		self.fw_info_file = fw_info_file
		self.start_file = "../app/start"
		self.user = user
		self.passwd = passwd
		
	#backup current FW in zip format
	def _backup_fw(self, dirs=''):
		if dirs:
			self.directory_list = dirs
		
		out_file = "fw_" + self.version + ".zip"
		zip_obj = ZipFile(out_file, 'w')
		
		print("[DEV] Backing up current FW, version ", self.version)
		
		os.chdir('../')
		for d in self.directory_list:
			for folderName, subfolders, filenames in os.walk(d):
				for filename in filenames:
					print("[DEV] Adding file: ", folderName + '/' + filename)
					filePath = os.path.join(folderName, filename)
					zip_obj.write(filePath)
		os.chdir('ota/')
		zip_obj.write(self.fw_info_file)
		zip_obj.close()
		
# 		os.rename(out_file, 'ota/' + out_file)
		self.backup_file = out_file
		
	#update FW information file with new FW
	def _update_fw_info(self, new_info):
		with open(self.fw_info_file, 'r') as f:
			content = json.loads(f.read())
			
		content["version"] = new_info[0]
		content["sequence_number"] = new_info[1]
		content["size"] = new_info[2]
		content["expiration_date"] = new_info[3]
		content["author"] = new_info[4]
		content["digital_signature"] = new_info[5]
		content["key_claims"] = new_info[6]
		content["checksum"] = new_info[7]
		content["backup"] = self.backup_file
		
		with open(self.fw_info_file, 'w') as f:
			f.write(json.dumps(content))
			
	# Return True if ver1 > ver2, False otherwise
	def _compare_versions(self, ver1, ver2):
		print('Version NEW: '+ str(ver1))
		print('Version OLD: '+ str(ver2))
		v1 = ver1.split('.')
		v2 = ver2.split('.')
		if v1[0] > v2[0]:
			return True
		if v1[0] == v2[0]:
			if v1[1] > v2[1]:
				return True
			if v1[1] == v2[1]:
				if v1[2] > v2[2]:
					return True
		return False
	
	def check_dependencies(self, deps_list):
		return True
	
	def check_device(self, device_type):
		return self.device == device_type
	
	def check_memory(self, fw_size):
		return True
	
	def check_min_version(self, req_version):
		if self.version == req_version:
			return True
		return self._compare_versions(self.version, req_version)
	
	def check_permissions(self, author):
		return True
	
	def check_sequence_number(self, seq_number):
		return int(self.sequence_number) < int(seq_number)
	
	def check_signature(self, signature, key_claims):
		return True
	
	def check_vendor(self, vendor_id):
		return True
	
	def check_version(self, new_version):
		return self._compare_versions(new_version, self.version)
	
	def check_version_list(self, req_version_list):
		if self.version in req_version_list:
			return True
		return False
	
	def download_firmware(self):
		print("[DEV] Retrieving FIRMWARE from Konker")
		#get manifest from addr
		r = requests.get('https://data.demo.konkerlabs.net/firmware/' + self.user + '/binary', auth=(self.user, self.passwd))
		print("[DEV] Status: ", r.status_code, r.reason)
		
		if r.status_code == 200:
			new_fw = r.content
			print("=======================================================")
			print(bytes(new_fw))
			print("=======================================================")
			
			return new_fw
		
		return ''
	
	def check_checksum(self, md5_recv, md5_calc):
		return md5_calc == md5_recv
	
	#backup old FW and extract new one
	def apply_firmware(self, new_fw, fw_info, steps=None):
		if steps:
			print("-> ", steps)
			
		self._backup_fw()
		
		#decompress new FW
		with ZipFile(new_fw, 'r') as zip_obj:
			zip_list = zip_obj.namelist()
			if 'fw_info.json' in zip_list:
				zip_obj.extract('fw_info.json')
				zip_list.remove('fw_info.json')
			zip_obj.extractall('../app/', zip_list)
		
		self._update_fw_info(fw_info)
		
	# write the new fw to flash
	def write_file(self, fw, version, alg):
		file_name = "fw_" + version + "." + alg
		with open(file_name, 'wb') as f:
			f.write(fw)
			
		return file_name
	
	# return True if its the first start of a new FW, False otherwise
	def check_first_start(self):
		if os.path.isfile(self.start_file):
			os.remove(self.start_file)
			return True
		return False
	
	def rollback(self):
		if os.path.isfile(self.backup_file):
			#decompress old FW
			os.chdir('../')
			with ZipFile(self.backup_file, 'r') as zip_obj:
				zip_list = zip_obj.namelist()
				if 'fw_info.json' in zip_list:
					zip_obj.extract('fw_info.json', 'ota/')
					zip_list.remove('fw_info.json')
				# extract fw_info file
				zip_obj.extractall(os.getcwd(), zip_list)
				
			os.chdir('ota')
			print("[DEV] Rollback done")
		else:
			print("[DEV] Backup does not exists!")
	
	# DOING...
	def send_message(self, msg):
		data = json.dumps({"update stage":msg})
		r = requests.post('http://data.demo.konkerlabs.net/pub/' + self.user + '/_update', auth=(self.user, self.passwd), data=data)
		print("[DEV] Sending: ", msg)
		
	def send_exception(self, exception):
		data = json.dumps({"update exception":exception})
		requests.post('http://data.demo.konkerlabs.net/pub/' + self.user + '/_update', auth=(self.user, self.passwd), data=data)
		print("[DEV] Exception: ", exception)
		
	def restart(self):
		print("[DEV] Reestarting FW")
		
		# create file to indicate the first start of a new FW
		with open(self.start_file, 'w') as f:
			f.write("1")
			
	def ping_platform():
		"""
		Returns True if host (str) responds to a ping request.
		Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
		"""
		host = 'konkerlabs.com'
		
		# Option for the number of packets as a function of
		param = '-n' if platform.system().lower()=='windows' else '-c'
	
		# Building the command. Ex: "ping -c 1 google.com"
		command = ['ping', param, '5', host]
	
		r = subprocess.run(command, stdout=subprocess.PIPE)
		print("Result:", r)
		
		r_str = str(r.stdout).split('\\')
# 		r_str = r_str.split('\\')
		print('>>> ', r_str[-2])
		
		return r_str[-2].split('/')[4]
	
	def measure_temp(self):
		temp = os.popen("vcgencmd measure_temp").readline()
		temp = temp.replace("'C","")
		
		return float((temp.replace("temp=","")))
	
	def get_device_status(self):
		cpu = psutil.cpu_percent()
		mem = psutil.virtual_memory().available 
		
		current_milli_time = lambda: int(round(time() * 1000))
		temp = self.measure_temp()
		
		return list([cpu, mem, temp, current_milli_time])
		
	# return True if all processes started correctly and communication is working, False otherwise
	def check_start(self):
		return True
