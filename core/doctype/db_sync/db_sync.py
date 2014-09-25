# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt
#sudo apt-get install sshpass
from __future__ import unicode_literals
import webnotes
from install_erpnext import exec_in_shell
from webnotes.utils import get_base_path, today
import os
import pxssh

from setup.page.setup_wizard.setup_wizard import import_core_docs
tables = ['tabPatient Register', 'tabPatient Encounter Entry', 'tabSingles', 'tabLead', 'tabEmployee', 'tabModality', 'tabStudy', 'tabCompany']
class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def sync_db(self, patient_id=None):
		cond = ''
		if patient_id:
			cond = self.get_cond(patient_id)
			# webnotes.errprint(cond)

		for table in tables:
			if cond:
				self.remote_to_local(table, cond, patient_id)
			else:
				self.remote_to_local(table, cond,patient_id)
				self.local_to_remote(table)
			webnotes.errprint("tab is %s "%patient_id)

	def remote_to_local(self, table, cond, patient_id):
		remote_settings = self.get_remote_settings(table, cond, patient_id)
		local_settings = self.get_local_settings(table)
		if table != 'tabSingles':
			try:
				# webnotes.errprint("""mysqldump --host='%(host_id)s' -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s -t --replace "%(tab)s" %(cond)s > %(file_path)s/up%(file_name)s.sql"""%remote_settings)
				# webnotes.errprint("""mysql -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s < %(file_path)s/up%(file_name)s.sql"""%local_settings)
				exec_in_shell("""mysqldump --host='%(host_id)s'  -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s -t --replace "%(tab)s" %(cond)s > %(file_path)s/up%(file_name)s.sql"""%remote_settings)
				exec_in_shell("""mysql -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s < %(file_path)s/up%(file_name)s.sql"""%local_settings)
				self.set_sync_date()
			except Exception as inst: 
				webnotes.msgprint(inst)

		if table == 'tabSingles':
			self.sync_active_status()

	def sync_active_status(self):
		import MySQLdb
		webnotes.errprint([self.doc.host_id, self.doc.remote_dbuser, self.doc.remote_dbuserpassword, self.doc.remote_dbname])
		db = MySQLdb.connect(self.doc.host_id, self.doc.remote_dbuser, self.doc.remote_dbuserpassword, self.doc.remote_dbname)
		cursor = db.cursor()
		is_active = cursor.execute("select value from `tabSingles` where doctype='Global Defaults' and field='is_active'")
		webnotes.errprint(is_active)
		webnotes.conn.sql("update tabSingles set value = '%s' where doctype='Global Defaults' and field='is_active'"%(is_active),debug=1)
		webnotes.conn.sql("commit")
		cursor.execute("commit")

	def local_to_remote(self, table):
		remote_settings = self.get_remote_settings(table)
		local_settings = self.get_local_settings(table)
		if table != 'tabSingles':
			try:
				webnotes.errprint("""mysql --host='%(host_id)s'  -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s < %(file_path)s/dw%(file_name)s.sql"""%remote_settings)
				webnotes.errprint("""mysqldump -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s -t --replace "%(tab)s" > %(file_path)s/dw%(file_name)s.sql"""%local_settings)
				exec_in_shell("""mysqldump -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s -t --replace "%(tab)s" > %(file_path)s/dw%(file_name)s.sql"""%local_settings)
				exec_in_shell("""mysql --host='%(host_id)s'  -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s < %(file_path)s/dw%(file_name)s.sql"""%remote_settings)
			except Exception as inst: pass

	def get_remote_settings(self, table, cond=None, patient_id=None):
		if cond:
			if table == 'tabPatient Register':
				cond = """--where="name='%s'" """%patient_id
			elif table == 'tabPatient Encounter Entry':
				cond = """--where="patient='%s'" """%patient_id

		return {'host_id':self.doc.host_id, 'host_ssh_user':self.doc.host_ssh_user, 'host_ssh_password':self.doc.host_ssh_password, 
			'remote_dbuser':self.doc.remote_dbuser, 'remote_dbuserpassword': self.doc.remote_dbuserpassword, 
			'remote_dbname': self.doc.remote_dbname, 'file_path':os.path.join(get_base_path(), "public", "files"), 'parameter':'%', 'file_name':table.replace(' ','_'),
			'tab': table, 'cond':cond if cond else ''}

	def get_local_settings(self, table):
		return {'dbuser':self.doc.dbuser, 'dbuserpassword': self.doc.dbuserpassword, 'dbname': self.doc.dbname, 'file_path':os.path.join(get_base_path(), "public", "files"),'file_name':table.replace(' ','_'), 'tab': table}

	def get_cond(self, patient_id):
		return """--where="name='%s'" """%patient_id

	def ledger_sync(self):
		unique_id = webnotes.conn.get_value("Global Defaults", None, "branch_id")
		acc_tables = ['tabCompany','tabFiscal Year', 'tabAccount', 'tabGL Entry']
		for table in acc_tables:
			if table == 'tabGL Entry':
				import MySQLdb
				db = MySQLdb.connect(self.doc.host_id, self.doc.remote_dbuser, self.doc.remote_dbuserpassword, self.doc.remote_dbname)
				cursor = db.cursor()
				webnotes.errprint("delete from `%(table)s` where name like '%(unique_id)s'"%{'table':table, "unique_id":'%%%s%%'%unique_id})
				cursor.execute("delete from `%(table)s` where name like '%(unique_id)s'"%{'table':table, "unique_id":'%%%s%%'%unique_id})
				cursor.execute("commit")
			self.local_to_remote(table)

	def set_sync_date(self):
		webnotes.conn.sql("update tabSingles set value = '%s' where doctype = 'Global Defaults' and field = 'last_sync_date'"%(today()))
		webnotes.conn.sql("commit")

	def main_server_sync(self):
		for tab in tables:
			if tab != 'tabSingles':
				exec_in_shell("""mysqldump --host='127.0.0.1'  -u medsyn_back3 -p'medsyn_back3' medsyn_back3 -t --replace "%(tab)s" %(cond)s > %(file_path)s/mainup%(file_name)s.sql"""%self.get_remote_settings(tab))
				exec_in_shell("""mysql -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s < %(file_path)s/mainup%(file_name)s.sql"""%self.get_local_settings(tab))

				exec_in_shell("""mysqldump -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s -t --replace "%(tab)s" > %(file_path)s/maindw%(file_name)s.sql"""%self.get_local_settings(tab))
				exec_in_shell("""mysql --host='127.0.0.1'  -u medsyn_back3 -p'medsyn_back3' medsyn_back3 < %(file_path)s/maindw%(file_name)s.sql"""%self.get_remote_settings(tab))

@webnotes.whitelist(allow_guest=True)
def sync_db_out():
	webnotes.msgprint("test")
	from webnotes.model.code import get_obj,get_server_obj
	get_obj('DB SYNC', 'DB SYNC').sync_db()