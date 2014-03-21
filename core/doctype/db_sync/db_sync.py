# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt
#sudo apt-get install sshpass
from __future__ import unicode_literals
import webnotes
from install_erpnext import exec_in_shell
from webnotes.utils import get_base_path
import os
import pxssh
tables = ['tabPatient Register', 'tabPatient Encounter Entry', 'tabPatient Report']
class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def sync_db(self, patient_id=None):
		# webnotes.errprint("from")
		cond = ''
		if patient_id:
			cond = self.get_cond(patient_id)
			# webnotes.errprint(cond)

		for table in tables:
			if cond:
				self.remote_to_local(table, cond)
			else:
				self.remote_to_local(table, cond)
				self.local_to_remote(table)
			# webnotes.errprint("tab is %s "%patient_id)

	def remote_to_local(self, table, cond):
		remote_settings = self.get_remote_settings(table, cond)
		local_settings = self.get_local_settings(table)
		try:
			# webnotes.errprint("""mysqldump --host='%(host_id)s' -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s -t --replace "%(tab)s" %(cond)s > %(file_path)s/up%(file_name)s.sql"""%remote_settings)
			exec_in_shell("""mysqldump --host='%(host_id)s' -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s -t --replace "%(tab)s" %(cond)s > %(file_path)s/up%(file_name)s.sql"""%remote_settings)
			exec_in_shell("""mysql -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s < %(file_path)s/up%(file_name)s.sql"""%local_settings)
		except Exception as inst: pass

	def local_to_remote(self, table):
		remote_settings = self.get_remote_settings(table)
		local_settings = self.get_local_settings(table)
		try:
			# webnotes.errprint("""mysqldump -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s -t --replace "%(tab)s" > %(file_path)s/dw%(file_name)s.sql"""%local_settings)
			exec_in_shell("""mysqldump -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s -t --replace "%(tab)s" > %(file_path)s/dw%(file_name)s.sql"""%local_settings)
			exec_in_shell("""mysql --host='%(host_id)s' -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s < %(file_path)s/dw%(file_name)s.sql"""%remote_settings)
		except Exception as inst: pass

	def get_remote_settings(self, table, cond=None):
		return {'host_id':self.doc.host_id, 'host_ssh_user':self.doc.host_ssh_user, 'host_ssh_password':self.doc.host_ssh_password, 
			'remote_dbuser':self.doc.remote_dbuser, 'remote_dbuserpassword': self.doc.remote_dbuserpassword, 
			'remote_dbname': self.doc.remote_dbname, 'file_path':os.path.join(get_base_path(), "public", "files"), 'parameter':'%', 'file_name':table.replace(' ','_'),
			'tab': table, 'cond':cond if cond else ''}

	def get_local_settings(self, table):
		return {'dbuser':self.doc.dbuser, 'dbuserpassword': self.doc.dbuserpassword, 'dbname': self.doc.dbname, 'file_path':os.path.join(get_base_path(), "public", "files"),'file_name':table.replace(' ','_'), 'tab': table}

	def get_cond(self, patient_id):
		return """--where="name='%s'" """%patient_id

	def ledger_sync(self):
		acc_tables = ['tabCompany','tabFiscal Year', 'tabAccounts', 'tabGL Entry']
		for table in acc_tables:
			if table == 'tabGL Entry':
				import MySQLdb
				db = MySQLdb.connect(self.doc.host_id, self.doc.remote_dbuser, self.doc.remote_dbuserpassword, self.doc.remote_dbname)
				cursor = db.cursor()
				cursor.execute("delete from `%(table)s`"%{'table':table})
				cursor.execute("commit")
			self.local_to_remote(table)
