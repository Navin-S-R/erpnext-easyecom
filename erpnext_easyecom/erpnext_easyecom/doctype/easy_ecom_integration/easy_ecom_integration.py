# Copyright (c) 2023, Aerele and contributors
# For license information, please see license.txt

import requests
import frappe
from frappe.model.document import Document
from bs4 import BeautifulSoup
from frappe import _

class EasyEcomIntegration(Document):
	pass

@frappe.whitelist()
def login_validation(url,email,password):
	easyecom_integration_settings=frappe.get_single('Easy Ecom Integration')
	if url==easyecom_integration_settings.url and email==easyecom_integration_settings.username and password==easyecom_integration_settings.password:
		password=easyecom_integration_settings.get_password("password")
		url = url
		body = {"email":email,"password":password}
		response = requests.post(
			url = url,
			json = body
		)
		if response.ok:
			payload = response.json()
			response_data=payload.get('data') or []
			if type(response_data) is list:
				return {"status":payload.get('message'),"jwt_token":None}
			elif type(response_data) is dict:
				return {"status":'Success',"jwt_token":payload.get('data').get('jwt_token') or None}
		else:
			error_content=response.__dict__
			soup=BeautifulSoup(error_content.get('_content'),'html.parser')
			error_code=soup.h1.string
			frappe.throw(f"Error code: {error_code}")
	else:
		frappe.throw("please save the document")

@frappe.whitelist()
def get_location(url,email,password,jwt_token):
	easyecom_integration_settings=frappe.get_single('Easy Ecom Integration')
	if url==easyecom_integration_settings.url and email==easyecom_integration_settings.username and password==easyecom_integration_settings.password:
		login_validations=login_validation(url,email,password) or None
		if login_validations:
			login=True if login_validations.get('status') == 'Success' else False
			if login==False:
				frappe.throw(login_validations.get('status'))
				    
		password=easyecom_integration_settings.get_password("password")
		jwt_token=f"Bearer {easyecom_integration_settings.jwt_token}"
		url = "https://api.easyecom.io/getAllLocation"
		headers = {"Authorization":jwt_token}
		response = requests.get(
				url = url,
				headers = headers
		)
		if response.ok:
			payload = response.json()
			if payload.get('message')=='Successful':
				response_data=payload.get('data') or []
				location_details=[]
				for row in response_data:
					row_dict={}
					row_dict['location']=row.get('location_name')
					row_dict['api_token']=row.get('api_token')
					billing_address=row.get('address type').get('billing_address')
					if billing_address:
						b_add=''
						billing_keys=billing_address.keys()
						for key in billing_keys:
							b_add+=(billing_address[key]+'\n')
					pickup_address=row.get('address type').get('pickup_address')
					if pickup_address:
						p_add=''
						pickup_keys=pickup_address.keys()
						for key in pickup_keys:
							p_add+=(pickup_address[key]+'\n')
					row_dict['billing_address']=b_add
					row_dict['pickup_address']=p_add
					location_details.append(row_dict)
				return location_details
		else:
			error_content=response.__dict__
			soup=BeautifulSoup(error_content.get('_content'),'html.parser')
			frappe.throw(soup.h1.string,title=_(soup.h2.string))
	else:
		frappe.throw("please save the document")


@frappe.whitelist()
def get_masters(url,email,password,jwt_token):
	easyecom_integration_settings=frappe.get_single('Easy Ecom Integration')
	if url==easyecom_integration_settings.url and email==easyecom_integration_settings.username and password==easyecom_integration_settings.password:
		master_details=[]
		msg=''
		login_validations=login_validation(url,email,password) or None
		if login_validations:
			login=True if login_validations.get('status') == 'Success' else False
			if login==False:
				frappe.throw(login_validations.get('status'))
				    
		password=easyecom_integration_settings.get_password("password")
		jwt_token=f"Bearer {easyecom_integration_settings.jwt_token}"
		url = "https://api.easyecom.io/Products/GetProductMaster"
		headers = {"Authorization":jwt_token}
		response = requests.get(
				url = url,
				headers = headers
		)
		if response.ok:
			payload = response.json()
			if type(payload.get('data')) is list:
				response_data=payload.get('data')
				if payload.get('nextUrl'):
					next_url=payload.get('nextUrl')
					while(next_url!=None):
						next_url,data=fetch_data_from_next_url(next_url,email,password,jwt_token)
						if data:
							response_data+=data
				normal_product_count=0
				if response_data:
					for row in response_data:
						if row.get('product_type')=='normal_product':
							normal_product_count+=1
					master_details.append({
						"master":"Items",
						"available_items":normal_product_count,
						"synced_items": 0
					})
		else:
			msg+='Got unexpected response on master Items \n'

		url = "https://api.easyecom.io/wms/V2/getVendors"
		headers = {"Authorization":jwt_token}
		response = requests.get(
				url = url,
				headers = headers
		)
		if response.ok:
			payload = response.json()
			if type(payload.get('data')) is list:
				response_data=payload.get('data')
				if payload.get('nextUrl'):
					next_url=payload.get('nextUrl')
					while(next_url!=None):
						next_url,data=fetch_data_from_next_url(next_url,email,password,jwt_token)
						if data:
							response_data+=data
				supplier_count = 0
				synced_count = 0
				if response_data:
					for row in response_data:
						supplier_count += 1
						create_supplier(row)
						synced_count += 1
					master_details.append({
						"master":"Supplier",
						"available_items":supplier_count,
						"synced_items": synced_count
					})
		else:
			msg+='Got unexpected response on master Supplier \n'

		url = "https://api.easyecom.io/Wholesale/v2/UserManagement?type=stn"
		headers = {"Authorization":jwt_token}
		response = requests.get(
				url = url,
				headers = headers
		)
		if response.ok:
			payload = response.json()
			if type(payload.get('data')) is list:
				response_data=payload.get('data')
				if payload.get('nextUrl'):
					next_url=payload.get('nextUrl')
					while(next_url!=None):
						next_url,data=fetch_data_from_next_url(next_url,email,password,jwt_token)
						if data:
							response_data+=data
				customer_count = 0
				synced_count = 0
				if response_data:
					for row in response_data:
						customer_count += 1
						n = create_customer(row)
						synced_count += n
					master_details.append({
						"master":"Customer",
						"available_items":customer_count,
						"synced_items": synced_count
					})
		if msg:
			return {"master_details":master_details,"msg":msg}
		else:
			return {"master_details":master_details,"msg":None}
	
	else:
		frappe.throw("please save the document")

##Fetch Item	
def fetch_data_from_next_url(next_url,email,password,jwt_token):
	url = "https://api.easyecom.io"+next_url
	headers = {"Authorization":jwt_token}
	response = requests.get(
			url = url,
			headers = headers
	)
	if response.ok:
		payload = response.json()
		if type(payload.get('data')) is list:
			response_data=payload.get('data')
			if payload.get('nextUrl'):
					next_url=payload.get('nextUrl')
					return next_url, response_data
			else:
				return None, response_data
		else:
			return None, []
	else:
		return None, []
	

def create_supplier(supplier_data):
	if not frappe.db.exists("Supplier",supplier_data['vendor_name']):
		new_supplier = frappe.get_doc({
		'doctype' : "Supplier",
		'supplier_name' : supplier_data['vendor_name'],
		'supplier_group' : "All Supplier Groups",
		'vendor_id' : supplier_data['vendor_c_id']
		}).insert()
		billing_address=supplier_data.get('address').get('billing')
		if billing_address:
			bill_addr = frappe.get_doc(
			{
			'doctype' : "Address",
			"address_line1" : billing_address['address'],
			"city" : billing_address['city'],
			"state" : billing_address['state_name'],
			"pincode" : billing_address['zip'],
			"links":[{
				"link_doctype" : "Supplier",
				"link_name" : new_supplier.name
			}]
			}).insert()
		dispatch_address=supplier_data.get('address').get('dispatch')
		if dispatch_address:
			dispatch_addr = frappe.get_doc(
			{
			'doctype' : "Address",
			'address_type' : "Shipping",
			'address_line1' : dispatch_address['address'],
			'city' : dispatch_address['city'],
			'state' : dispatch_address['state_name'],
			'pincode' : dispatch_address['zip'],
			'links':[
			{
				"link_doctype" : "Supplier",
				"link_name" : new_supplier.name
			}]
			}).insert()
	return 1

def create_customer(customer_data):
	if not frappe.db.exists("Customer",customer_data['companyname']):
		new_customer = frappe.get_doc({
		'doctype' : "Customer",
		'customer_name' : customer_data['companyname'],
		'customer_type' : "Company",
		'tax_id' : customer_data['gstNum'],
		'territory' : 'All Territories',
		'customer_group' : 'Commercial'
		}).insert()
		bill_addr = frappe.get_doc(
		{
		'doctype' : "Address",
		"address_line1" : customer_data["billingStreet"],
		"city" : customer_data['billingCity'],
		"country" : customer_data['billingCountry'],
		"state" : customer_data['billingState'],
		"pincode" : customer_data['billingZipcode'],
		"links":[{
			"link_doctype" : "Customer",
			"link_name" : new_customer.name
		}]
		}).insert()
		dispatch_addr = frappe.get_doc(
		{
		'doctype' : "Address",
		'address_type' : "Shipping",
		'address_line1' : customer_data['dispatchStreet'],
		'city' : customer_data['dispatchCity'],
		"country" : customer_data['dispatchCountry'],
		'state' : customer_data['dispatchState'],
		'pincode' : customer_data['dispatchZipcode'],
		'links':[
		{
			"link_doctype" : "Customer",
			"link_name" : new_customer.name
		}]
		}).insert()
	return 1
