# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import webnotes
from install_erpnext import exec_in_shell
from webnotes.model.doc import addchild
from webnotes.model.bean import getlist
import os

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def show_sites(self):
		self.doclist=self.doc.clear_table(self.doclist,'site_status_details')
		for filename in os.listdir(self.doc.sites_path):
			sites = addchild(self.doc, 'site_status_details',
				'Site Status Details', self.doclist)
			sites.site_name = filename
			if filename[-1] != '1':
				sites.status = '1'

	def make_enable_dissable(self):
		for site in getlist(self.doclist, 'site_status_details'):
			#make dissable
			if site.status not in [1, '1'] and site.site_name[-1] != '1':
				exec_in_shell("mv %(path)s/%(site_name)s/ %(path)s/%(site_name)s1"%{'path':self.doc.sites_path,'site_name':site.site_name})
				self.update_site_details(site.site_name[-1], 0)

			#make enable
			if site.status == 1 and site.site_name[-1] == '1':
				new_site_name = site.site_name[:-1]
				exec_in_shell("mv %(path)s/%(site_name)s/ %(path)s/%(new_site_name)s"%{'path':self.doc.sites_path,'site_name':site.site_name, 'new_site_name':new_site_name})
				self.update_site_details(site.site_name[-1], 1)
		self.show_sites()
		self.doc.save()

	def update_site_details(self, site_name, status):
		webnotes.conn.sql("update `tabSite Details` set is_active = '%s' where name = '%s'"%(status, site_name))
		db_details = webnotes.conn.sql("select database_name, database_password from `tabSite Details` where name = '%s'"%(site_name),as_list=1)
		self.test_db(db_details[0][0], db_details[0][1], status)
		webnotes.conn.sql("commit")

	def test_db(self):		
		import MySQLdb
		myDB = MySQLdb.connect(user="%s"%user,passwd="%s"%pwd,db="%s"%user)
		cHandler = myDB.cursor()
		cHandler.execute("update `tabSingles` set is_active = '%s' where doctype='Global Defaults'"%(status))
		cHandler.execute("commit")


