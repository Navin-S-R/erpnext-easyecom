// Copyright (c) 2023, Aerele and contributors
// For license information, please see license.txt

frappe.ui.form.on('Easy Ecom Integration', {
	refresh: function(frm) {
		if (!frm.doc.__islocal){
			if(frm.doc.username && frm.doc.url && frm.doc.password){
				frm.add_custom_button(__('Validate Login'), function() {
					frappe.call({
						method: "erpnext_easyecom.erpnext_easyecom.doctype.easy_ecom_integration.easy_ecom_integration.login_validation",
						args:{
							url:frm.doc.url,
							email:frm.doc.username,
							password:frm.doc.password
						},
						callback: function (r) {
							if(r.message) {
								if(r.message["status"] == "Success"){
									frm.set_value("jwt_token", r.message["jwt_token"]);
									frm.set_value("api_token", r.message["api_token"]);
									frm.refresh_field("jwt_token");
									frm.refresh_field("api_token");
									frm.save()
									frappe.show_alert({
										message: __("Login Verified"),
										indicator: "green",
									});
									
								}
								else if(r.message["status"] != "Success"){
									frm.set_value("jwt_token", r.message["jwt_token"]);
									frm.set_value("api_token", r.message["api_token"]);
									frm.refresh_field("jwt_token");
									frm.refresh_field("api_token");
									frm.save()
									frappe.show_alert({
										message: __(r.message["status"]),
										indicator: "red",
									});
								}
							}
						}
					})
				}).addClass("btn-primary");
			}
			if(frm.doc.username && frm.doc.url && frm.doc.password && frm.doc.jwt_token){
				frm.add_custom_button(__('Get Location'), function() {
					frappe.call({
						method: "erpnext_easyecom.erpnext_easyecom.doctype.easy_ecom_integration.easy_ecom_integration.get_location",
						args:{
							url:frm.doc.url,
							email:frm.doc.username,
							password:frm.doc.password,
							jwt_token:frm.doc.jwt_token
						},
						callback: function (r) {
							if(r.message) {
								cur_frm.set_value('location_details',[])
								for(let i = 0; i<r.message.length;i++){
									cur_frm.add_child("location_details")
									frappe.model.set_value(frm.doc.location_details[i].doctype,frm.doc.location_details[i].name,"location",r.message[i]['location'])
									frappe.model.set_value(frm.doc.location_details[i].doctype,frm.doc.location_details[i].name,"api_token",r.message[i]['api_token'])
									frappe.model.set_value(frm.doc.location_details[i].doctype,frm.doc.location_details[i].name,"billing_address",r.message[i]['billing_address'])
									frappe.model.set_value(frm.doc.location_details[i].doctype,frm.doc.location_details[i].name,"pickup_address",r.message[i]['pickup_address'])
								}
								frm.refresh_field("location_details");
								frm.save();
							}
						}
					})
				}).addClass("btn-primary").css({'color':'white','background-color': 'grey','font-weight': 'bold'});
			}
			if(frm.doc.username && frm.doc.url && frm.doc.password && frm.doc.jwt_token){
				frm.add_custom_button(__('Get Masters'), function() {
					frappe.call({
						method: "erpnext_easyecom.erpnext_easyecom.doctype.easy_ecom_integration.easy_ecom_integration.get_masters",
						args:{
							url:frm.doc.url,
							email:frm.doc.username,
							password:frm.doc.password,
							jwt_token:frm.doc.jwt_token
						},
						freeze: true,
						freeze_message: "Fetching Masters. Please wait for few seconds...",
						callback: function (r) {
							if(r.message) {
								if(r.message["master_details"]){
									cur_frm.set_value('master_details',[])
								for(let i = 0; i<r.message['master_details'].length;i++){
									cur_frm.add_child("master_details")
									frappe.model.set_value(frm.doc.master_details[i].doctype,frm.doc.master_details[i].name,"master",r.message['master_details'][i]['master'])
									frappe.model.set_value(frm.doc.master_details[i].doctype,frm.doc.master_details[i].name,"available_items",r.message['master_details'][i]['available_items'])
									frappe.model.set_value(frm.doc.master_details[i].doctype,frm.doc.master_details[i].name,"synced_items",r.message['master_details'][i]['synced_items'])
								}
								frm.refresh_field("master_details");
								frm.save();
								frappe.show_alert({
									message: __("Masters Fetched and Synced Successfully."),
									indicator: "green",
								});
								}
							}
							// else {
							// 	frappe.show_alert({
							// 		message: __(r.message["status"]),
							// 		indicator: "red",
							// 	});
							// }
						}
					})
				}).addClass("btn-primary").css({'color':'white','background-color': 'grey','font-weight': 'bold'});
			}
		}
	}
});
