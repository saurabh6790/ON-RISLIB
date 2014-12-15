# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt
#sudo apt-get install sshpass
from __future__ import unicode_literals
import webnotes
from install_erpnext import exec_in_shell
from webnotes.utils import get_base_path, today, cint
import os
import MySQLdb
# import pxssh

from webnotes.utils import cint, cstr, getdate, now, nowdate, get_defaults
from setup.page.setup_wizard.setup_wizard import import_core_docs
tables = ['tabPatient Register', 'tabPatient Encounter Entry', 'tabSingles', 'tabLead', 'tabEmployee', 'tabModality', 'tabStudy', 'tabCompany']
class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def sync_db(self, patient_id=None):
		if not (os.path.exists(os.path.join(get_base_path(), "public", 'dbsync.txt'))):
			self.validate_tenant()
			self.initiate_sync_db(patient_id)
		else:
			self.initiate_sync_db(patient_id)

	def validate_tenant(self):
		tenant_list = [] 
		if self.doc.host_id and self.doc.remote_dbuser and self.doc.remote_dbuserpassword and self.doc.remote_dbname:
			db = MySQLdb.connect('eiims.medsynaptic.com', 'ris', '6xkWqXZ1PtUSVfJj', 'ris')
			cursor = db.cursor()
			
			tab = self.get_tab(self.doc.host_id, cursor)
			
			if tab:
				cursor.execute("select no_of_offline_tenant from %s where %s = '%s' "%(tab['tab'], tab['field'], self.doc.host_id))		
				no_of_offline_tenant = cursor.fetchone()
				
				cursor.execute("select ifnull(offline_tenant_id, '') from %s where %s = '%s' "%(tab['tab'], tab['field'], self.doc.host_id))		
				offline_tenant_id = cursor.fetchone()
				
				if no_of_offline_tenant:
					if cint(no_of_offline_tenant[0][0]) > 0:
						if offline_tenant_id:
							
							tenant_list = offline_tenant_id[0].split(',')

						if len(tenant_list) == cint(no_of_offline_tenant[0][0]):
							webnotes.msgprint("Tenat Limit Exceeded!!!", raise_exception=1)
						else:
							branch_id = webnotes.conn.get_value('Global Defaults', None, 'branch_id')
							tenant_list.append(branch_id)
							
							cursor.execute("Update %s set offline_tenant_id = '%s' where %s = '%s'"%(tab['tab'], ','.join(x for x in tenant_list if x), tab['field'], self.doc.host_id))
							cursor.execute("commit")
					else:
						webnotes.msgprint("Offline tenant not register with this system", raise_exception=1)
				else:
					webnotes.msgprint("Offline tenant not register with this system", raise_exception=1)
	
	def get_tab(self, host_id, cursor):
		cursor.execute("select true from `tabSite Details` where name = '%s'"%(host_id))
		is_tenant = cursor.fetchone()

		if is_tenant:
			return {'tab': '`tabSite Details`', 'field':'name'}

		cursor.execute("select true from `tabSub Tenant Details` where sub_tenant_url = '%s'"%(host_id))
		is_tenant = cursor.fetchone()

		if is_tenant:
			return {'tab':'`tabSub Tenant Details`', 'field': 'sub_tenant_url'}

		else:
			webnotes.msgprint('Tenant Not Yet Registered',raise_exception=1)

	def initiate_sync_db(self, patient_id=None):
		cond = ''
		if patient_id:
			cond = self.get_cond(patient_id)
			# webnotes.errprint(cond)

		for table in tables:
			if cond:
				self.remote_to_local(table, cond, patient_id)
			else:
				# self.remote_to_local(table, cond,patient_id)
				self.local_to_remote(table)
			# webnotes.errprint("tab is %s "%patient_id)	

	def remote_to_local(self, table, cond, patient_id):
		remote_settings = self.get_remote_settings(table, cond, patient_id)
		local_settings = self.get_local_settings(table)
		if table != 'tabSingles':
			try:
				# webnotes.errprint("""mysqldump --host='%(host_id)s' -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s -t --replace "%(tab)s" %(cond)s > %(file_path)s/up%(file_name)s.sql"""%remote_settings)
				# webnotes.errprint("""mysql -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s < %(file_path)s/up%(file_name)s.sql"""%local_settings)
				exec_in_shell("""mysqldump --host='%(host_id)s'  -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s -t --replace "%(tab)s" %(cond)s > %(file_path)s/up%(file_name)s.sql"""%remote_settings)
				exec_in_shell("""mysql -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s < %(file_path)s/up%(file_name)s.sql"""%local_settings)
			except Exception as inst: 
				webnotes.msgprint(inst, raise_exception=1)

		if table == 'tabSingles':
			self.sync_active_status()

	def sync_active_status(self):
		is_active = ''
		webnotes.errprint([self.doc.host_id, self.doc.remote_dbuser, self.doc.remote_dbuserpassword, self.doc.remote_dbname])
		db = MySQLdb.connect(self.doc.host_id, self.doc.remote_dbuser, self.doc.remote_dbuserpassword, self.doc.remote_dbname)
		cursor = db.cursor()
		cursor.execute("select value from `tabSingles` where doctype='Global Defaults' and field='is_active'")
		is_active = cursor.fetchone()
		webnotes.conn.sql("update tabSingles set value = '%s' where doctype='Global Defaults' and field='is_active'"%(is_active[0]),debug=1)
		webnotes.conn.sql("commit")
		cursor.execute("commit")

	def local_to_remote(self, table):
		remote_settings = self.get_remote_settings(table)
		local_settings = self.get_local_settings(table)
		if table != 'tabSingles':
			try:
				# webnotes.errprint("""mysql --host='%(host_id)s'  -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s < %(file_path)s/dw%(file_name)s.sql"""%remote_settings)
				# webnotes.errprint("""mysqldump -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s -t --replace "%(tab)s" > %(file_path)s/dw%(file_name)s.sql"""%local_settings)
				exec_in_shell("""mysqldump -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s -t --replace "%(tab)s" > %(file_path)s/dw%(file_name)s.sql"""%local_settings)
				exec_in_shell("""mysql --host='%(host_id)s'  -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s < %(file_path)s/dw%(file_name)s.sql"""%remote_settings)
				self.set_sync_date()
			except Exception as inst:
				webnotes.msgprint(inst, raise_exception=1)

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
				# webnotes.errprint("delete from `%(table)s` where name like '%(unique_id)s'"%{'table':table, "unique_id":'%%%s%%'%unique_id})
				cursor.execute("delete from `%(table)s` where name like '%(unique_id)s'"%{'table':table, "unique_id":'%%%s%%'%unique_id})
				cursor.execute("commit")
			self.local_to_remote(table)

	def get_salt(self):
		import os, base64
		return base64.b64encode(os.urandom(32))			

	def encrypt(self,key, msg):
		encryped = []
		for i, c in enumerate(msg):
			key_c = ord(key[i % len(key)])
			msg_c = ord(c)
			encryped.append(chr((msg_c + key_c) % 127))
		return ''.join(encryped)		

	def set_sync_date(self):
		# webnotes.errprint("in the sync_db")
		file_path=os.path.join(get_base_path(), "public")
		# webnotes.errprint(file_path+'/'+"dbsync.txt")
		f2=file_path+'/'+"dbsync.txt"
		salt = self.get_salt()
		digest = self.encrypt(salt,cstr(today()))
		file = open(f2, "w+")
		file.write(digest)
		file.write(",")
		file.write(salt)
		file.close()
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
	from webnotes.model.code import get_obj,get_server_obj
	get_obj('DB SYNC', 'DB SYNC').sync_db()