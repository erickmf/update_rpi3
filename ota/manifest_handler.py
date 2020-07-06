#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 14:28:43 2020

@author: majubs
"""
import sys, json, requests, hashlib, os
import pi3_device as pi3
from time import sleep

class Manifest:
	errors_msg = [
		"Older version",
		"Update for different device",
		"Older sequence number",
		"Firmware URL missing",
		"Key claims missing"
		"Invalid digital signature",
		"Checksum missing",
		"Vendor ID invalid",
		"Not enough memory to update",
		"Minimum required version not found",
		"Version not in required version list",
		"Dependencies not met",
		"Author does not have permission"]
	
	def __init__(self,user,passwd):
		self.m_json = {}
		self.m_parsed = {}
		self.required_elements = ["version", "device", "sequence_number", "key_claims", "digital_signature", "checksum"]
		self.optional_elements = ["fw_url","vendor_id", "size", "required_version", "required_version_list", "dependencies", "author", "firmware", "payload_format", "processing_steps", "additional_steps", "encryption_wrapper"]
		self.valid = True
		self.user = user
		self.passwd = passwd
		
	def _print_errors(self, err_filter):
		print("Errors parsing manifest:", err_filter)
		errs = [e for (e, i) in zip(self.errors_msg, err_filter) if i]
		for e in errs:
			print("[ERRROR]", e)
	
	def get_manifest(self):
		print("Retrieving manifest from Konker Platform")
		try:
			r = requests.get('http://data.demo.konkerlabs.net/sub/' + self.user + '/_update', auth=(self.user, self.passwd))
		except:
			return False
		#get manifest from addr
		print("Status: ", r.status_code, r.reason)
		
		if r.status_code == 200:
			self.m_json = r.json()[0]['data']
			#r = r.text.replace("\'", "\"")
			#self.m_json = json.loads(r)
# 			print(json.dumps(self.m_json, indent=4))
			
			return True
		
		return False
	
	def parse_manifest(self, device):
		print("Parsing and validating manifest")
		
		# check_errs will de used as a filter for error messages, a True element means error ocurred
		# device.check_* functions return True if check is OK
		# so check_errs elements receive the negated result of device.check_* funtions
		check_errs =  []
		for field in self.required_elements:
			print("Check for required element ", field)
			if field in self.m_json and self.m_json.get(field) != None:
				if field == "version":
					check_errs.append(not device.check_version(self.m_json.get(field)))
				elif field == "device":
					check_errs.append(not device.check_device(self.m_json.get(field)))
				elif field == "sequence_number":
					check_errs.append(not device.check_sequence_number(self.m_json.get(field)))
				elif field == "digital_signature":
					check_errs.append(not device.check_signature(self.m_json.get(field), self.m_json.get("key_claims")))
				else: #will be used later
					check_errs.append(False)
					self.m_parsed[field] = self.m_json.get(field)
			else:
				print("Required element missing from manifest: ", field)
				check_errs.append(True)
# 				self.valid = False
			
# 		print(">>> Required elements: ", self.valid)
		for field in self.optional_elements:
			print("Checking for optional element ", field)
			if field in self.m_json and self.m_json.get(field) != None:
				if field == "vendor_id":
					check_errs.append(not device.check_vendor(self.m_json.get(field)))
				elif field == "size":
					check_errs.append(not device.check_memory(self.m_json.get(field)))
				elif field == "required_version":
					check_errs.append(not device.check_min_version(self.m_json.get(field)))
				elif field == "required_version_list":
					check_errs.append(not device.check_version_list(self.m_json.get(field)))
				elif field == "dependencies":
					check_errs.append(not device.check_dependencies(self.m_json.get(field)))
				elif field == "author":
					check_errs.append(not device.check_permissions(self.m_json.get(field)))
				else:
					check_errs.append(False)
					self.m_parsed[field] = self.m_json.get(field)
			else:
				print("Optional element NOT in manifest: ", field)
		
		# check if any error occured
		incorrect = False
		for e in check_errs:
			incorrect = incorrect or e #one True will chance incorrect to True
		if incorrect:
			self.valid = False
			self._print_errors(check_errs)
	
	def apply_manifest(self, device):
		print("Applying manifest!")
		#update FW
		print(self.m_parsed)
		new_fw = device.download_firmware()
		if new_fw == '':
			device.send_exception("Firmware not found")
			print("Did not receive any content")
			return False
		else:
			open('temp_fw.zip', 'wb').write(new_fw)
		
		md5sum = hashlib.md5(bytes(new_fw)).hexdigest()
		print("Received file checksum >>> ", md5sum)
		if device.check_checksum(self.m_parsed['checksum'], md5sum):
			device.send_message("Firmware received correctly. Checksum OK")
			print("Checksum correct!")
		else:
			device.send_exception("Checksum did not match")
			print("Checksum incorrect!")
			return
		
		#do post update stuff (if needed)
		if 'processing_steps' in self.m_parsed:
			print("Doing processing steps: ", self.m_parsed['processing_steps'][0])
			p_steps = self.m_parsed['processing_steps'][0]
			if p_steps.get('decode_algorithm'):
				new_fw = device.write_file(new_fw, self.m_json.get('version'), p_steps['decode_algorithm'])
		
		if 'additional_steps' in self.m_parsed:
			print("Doing addtional steps: ", self.m_parsed['additional_steps'][0])
		
		#substitute fw
		print("Applying new firmware")
		device.apply_firmware('temp_fw.zip', (self.m_json.get("version"), self.m_json.get("sequence_number"), self.m_json.get("size"), self.m_json.get("expiration_date"), self.m_json.get("author"), self.m_json.get("digital_signature"), self.m_json.get("key_claims"), self.m_json.get("checksum")))
		os.remove('temp_fw.zip')
		
		return True

def read_last_conf():
	conf = ''
	try:
		with open('config.json', 'r') as infile:
			conf = json.load(infile)
	# Do something with the file
	except IOError:
		print("Configuration file not found. Cannot access platform.")
	
	return conf

def main(argv):
	print("Starting manifest parser")
	configuration = read_last_conf()
	
	if configuration == '':
		return
	
	user = configuration['user']
	passwd = configuration['pwd']
	
	M = Manifest(user,passwd)
	D = pi3.Device(user,passwd)
	
	net_info = D.get_network_info()
	D.send_message(net_info)
	status = list([D.get_device_status()])
	
	# check if its the first start of a new FW
	if D.check_first_start():
		print("Starting a new FW")
		if D.check_start():
			print("New version: ", D.version)
			status.append(D.get_device_status())
			D.send_message("Update correct")
		else:
			print("New FW did not start correctly")
			D.send_exception("Update incorrect")
			D.rollback()
		return
	else:
		print("Starting OTA process")
	
	if M.get_manifest():
		status.append(D.get_device_status())
		D.send_message("Manifest received")
		M.parse_manifest(D)
		if M.valid:
# 			sleep(2)
			status.append(D.get_device_status())
			D.send_message("Manifest correct")
			if M.apply_manifest(D):
				print("Update finished!")
				status.append(D.get_device_status())
				D.send_message("Rebooting")
				D.restart()
		else:
			D.send_exception("Manifest incorrect")
			print("Manifest format is incorrect")
	else:
		D.send_exception("Could not get manifest")
		print("Could not get manifest from Konker")
		
	D.send_device_status(status)

if __name__ == "__main__":
	main(sys.argv)
