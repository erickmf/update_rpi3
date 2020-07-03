#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 16:04:38 2020

@author: majubs
"""
import hashlib
import http.server as serv
import socketserver, socket, os, json
from urllib.parse import urlparse, parse_qs
from Crypto.PublicKey import RSA

# Handler = serv.SimpleHTTPRequestHandler

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
IP = s.getsockname()[0]

def generate_keys():
	key = RSA.generate(2048)
	pubkey = key.publickey()
	
	return key, pubkey

def get_json():
	file = "new_fw/manifest_test.json"
	content = ""
	key, pubkey = generate_keys()
# 	print("Looking for file: ", file)
	if(os.path.isfile(file)):
		print("Reading contents from file: ", file)
		with open(file) as f:
			content = json.load(f)
			content["digital_signature"] = pubkey.exportKey().decode('utf8')
# 				md5 = hashlib.md5()
# 				md5.update(json.dumps(content).encode('utf8'))
# 				content["checksum"] =  'fe2e61db2a66ad832f08bc84bcf9c18d' #md5.hexdigest
			
# 				print("File constents updated: ")
# 				print(json.dumps(content, indent=4))
	else:
		print("File does not exist")
		
	return content

def get_file():
	file = "new_fw/new_app.zip"
	content = ""
# 	print("Looking for file: ", file)
	if(os.path.isfile(file)):
		print("Reading contents from file: ", file)
		with open(file, 'rb') as f:
			content = f.read()
				
# 				print("File constents updated: ")
# 				print(json.dumps(content, indent=4))
	else:
		print("File does not exist")
		
	return content

class MyHttpRequestHandler(serv.SimpleHTTPRequestHandler):
	def do_GET(self):
		print("GET received")
		if self.path == '/':
			self.path = '/new_fw'
		
		# Extract query param
		query_components = parse_qs(urlparse(self.path).query)
		print("--------------> ", query_components)
		if 'file' in query_components:
			file = query_components["file"][0]
		else:
			return serv.SimpleHTTPRequestHandler.do_GET(self)

		# Get the correct file to be sent
		if file == '0':   # send manifest
			json_file = get_json()
		
			if json_file == "":
				self.send_response(404)
				return
	
			# Sending an '200 OK' response
			self.send_response(200)
	
			# Setting the header
			self.send_header("Content-type", "application/json")
	
			# Whenever using 'send_header', you also have to call 'end_headers'
			self.end_headers()
	
			# Writing the HTML contents with UTF-8
			print("Sending contents: ", json_file)
			self.wfile.write(bytes(str(json_file), "utf8"))
		elif file == '1':    # send firmware
			print("Sending new firmware")
			file = get_file()
		
			if file == "":
				self.send_response(404)
				return
	
			# Sending an '200 OK' response
			self.send_response(200)
	
			# Setting the header
			self.send_header("Content-type", "text/plain")
	
			# Whenever using 'send_header', you also have to call 'end_headers'
			self.end_headers()
	
			# Writing the binary contents with bytes
			print("Sending contents: ", file)
			self.wfile.write(bytes(file))
		else:
			print("Cannot find requested file")
			self.send_response(404)

		return
	
# actual server
Handler = MyHttpRequestHandler
PORT = 8084

with socketserver.TCPServer((IP, PORT), Handler) as httpd:
	print("Server at", IP, PORT)
	httpd.serve_forever()
