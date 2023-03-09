# Copyright (c) 2023, Aerele and contributors
# For license information, please see license.txt

import requests
import frappe
from frappe.model.document import Document
from bs4 import BeautifulSoup
from frappe import _
from frappe.utils import get_link_to_form

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
				synced_item=0
				if response_data:
					for row in response_data:
						if row.get('product_type')=='normal_product':
							normal_product_count+=1
							create_item=create_item_details(row)
							synced_item+=1 if create_item else 0

					master_details.append({
						"master":"Items",
						"available_items":normal_product_count,
						"synced_items": synced_item
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
	
####Create Easy Ecom Item and Erp item
def create_item_details(row):
	try:
		if not frappe.db.exists("Easy Ecom Item",str(row.get('cp_id'))):
			easyecom_item=frappe.get_doc({
					'doctype': 'Easy Ecom Item',
					'cp_id': str(row.get('cp_id')),
					'product_id': row.get('product_id'),
					'sku':row.get('sku'),
					'product_name': row.get('product_name'),
					'description':row.get('description'),
					'active':row.get('active'),
					'inventory':row.get('inventory'),
					'product_type':row.get('product_type'),
					'brand':row.get('brand'),
					'colour':row.get('colour'),
					'category_id':row.get('category_id'),
					'brand_id':row.get('brand_id'),
					'accounting_sku':row.get('accounting_sku'),
					'accounting_unit':row.get('accounting_unit'),
					'category_name':row.get('category_name'),
					'expiry_type':row.get('expiry_type'),
					'company_name':row.get('company_name'),
					'c_id':row.get('c_id'),
					'height':row.get('height'),
					'width':row.get('width'),
					'length':row.get('length'),
					'weight':row.get('weight'),
					'cost':row.get('cost'),
					'mrp':row.get('mrp'),
					'size':row.get('size'),
					'cp_sub_products_count':row.get('cp_sub_products_count'),
					'model_no':row.get('model_no'),
					'hsn_code':row.get('hsn_code'),
					'tax_rate':row.get('tax_rate'),
					'product_shelf_life':row.get('product_shelf_life'),
					'product_image_url':row.get('product_image_url'),
					'cp_inventory':row.get('cp_inventory')
				}).insert()
			
			if not frappe.db.exists("Item",{'easy_ecom_item':str(row.get('cp_id'))}):
				if row.get('brand') and not frappe.db.exists("Brand",{'name':row.get('brand')}):
					frappe.get_doc({
						'doctype':'Brand',
						'brand':row.get('brand')
					}).insert()
				erp_item=frappe.get_doc({
					'doctype': 'Item',
					'easy_ecom_item':str(row.get('cp_id')),
					'item_code':str(row.get('cp_id')),
					'item_name':str(row.get('product_name'))+str(row.get('model_no')),
					'item_group':'All Item Groups',
					'stock_uom':'Nos',
					'disabled': 0 if row.get('active') else 1,
					'description':row.get('description'),
					'brand':row.get('brand') or 'Unknown'
				}).insert()
			easyecom_item.erp_item_code=erp_item.name
			easyecom_item.erp_item_code_link=get_link_to_form('Easy Ecom Item',erp_item.name)
			easyecom_item.save()
		return True
	except:
		return False
	
def create_supplier(supplier_data):
	try:
		if not frappe.db.exists("Supplier",supplier_data['vendor_name']):
			new_supplier = frappe.get_doc({
			'doctype' : "Supplier",
			'supplier_name' : supplier_data.get('vendor_name'),
			'supplier_group' : "All Supplier Groups",
			'vendor_id' : supplier_data.get('vendor_c_id')
			}).insert()
			billing_address=supplier_data.get('address').get('billing')
			if billing_address:
				bill_addr = frappe.get_doc(
				{
				'doctype' : "Address",
				"address_line1" : billing_address.get('address'),
				"is_primary_address" : 1,
				"city" : billing_address.get('city'),
				"state" : billing_address.get('state_name'),
				"pincode" : billing_address.get('zip'),
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
				"is_shipping_address" : 1,
				'address_line1' : dispatch_address.get('address'),
				'city' : dispatch_address.get('city'),
				'state' : dispatch_address.get('state_name'),
				'pincode' : dispatch_address.get('zip'),
				'links':[
				{
					"link_doctype" : "Supplier",
					"link_name" : new_supplier.name
				}]
				}).insert()
		return 1
	except:
		return 0

def create_customer(customer_data):
	try:
		if not frappe.db.exists("Customer",customer_data.get('companyname')):
			new_customer = frappe.get_doc({
			'doctype' : "Customer",
			'customer_name' : customer_data.get('companyname'),
			'customer_type' : "Company",
			'tax_id' : customer_data.get('gstNum'),
			'territory' : 'All Territories',
			'customer_group' : 'Commercial'
			}).insert()
			bill_addr = frappe.get_doc(
			{
			'doctype' : "Address",
			"address_line1" : customer_data.get("billingStreet"),
			"city" : customer_data.get('billingCity'),
			"country" : customer_data.get('billingCountry'),
			"state" : customer_data.get('billingState'),
			"pincode" : customer_data.get('billingZipcode'),
			"is_primary_address" : 1,
			"links":[{
				"link_doctype" : "Customer",
				"link_name" : new_customer.name
			}]
			}).insert()
			dispatch_addr = frappe.get_doc(
			{
			'doctype' : "Address",
			'address_type' : "Shipping",
			"is_shipping_address" : 1,
			'address_line1' : customer_data.get('dispatchStreet'),
			'city' : customer_data.get('dispatchCity'),
			"country" : customer_data.get('dispatchCountry'),
			'state' : customer_data.get('dispatchState'),
			'pincode' : customer_data.get('dispatchZipcode'),
			'links':[
			{
				"link_doctype" : "Customer",
				"link_name" : new_customer.name
			}]
			}).insert()
		return 1
	except:
		return 0