#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
# Script para manipular credenciais e conectar na plataforma da Konker
#
# @author: Majubs
################################################################################

import requests, json, os

class Platform:
	# variables here are shared by all objects of the Platform class (Caution!)
	api = 'https://api.demo.konkerlabs.net/v1'
	header = {"Accept":"*/*", "Authorization": "Bearer {}"}
	params = {"application": "default", "deviceModelName": "default"}
	token_file = "token.txt"
	token_url = "/oauth/token"
	token_params = {"grant_type":"client_credentials", "client_id": "", "client_secret": ""}
	
	def __init__(self, user, pwd, api='', header='', params=''):
		# variables unique to an object can be instantiated here
		if(api):
			self.api = api
			self.token_url = api + self.token_url
		if(header):
			self.header = header
		if(params):
			self.params = params
		self.credentials = self.get_access_token(user, pwd)
		self.header['Authorization'] = self.header['Authorization'].format(self.credentials['access_token'])

	# Access token
	def get_access_token(self, user, pwd):
		self.token_params["client_id"] = user
		self.token_params["client_secret"] = pwd
		
		if(os.path.isfile(self.token_file)):
			print("Reading access token from file: ", self.token_file)
			with open(self.token_file) as f:
				cred = json.load(f)
		else:
			# Get credentials
			cred = requests.post(url=self.token_url, params=self.token_params)
			if cred.status_code != 200:
				print("Failed to get Access Token! Code = ", cred.status_code)
			else:
				cred = cred.json()
				with open(self.token_file, 'w') as f:
					json.dump(cred, f)
				print("Access token saved to file: ", self.token_file)

	#	print("Credentials:")
	#	print(json.dumps(cred, indent=4))
	
		return cred