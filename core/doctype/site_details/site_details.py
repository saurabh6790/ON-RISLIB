# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import webnotes
import os
from webnotes.utils import get_base_path
from install_erpnext import exec_in_shell, create_user, parse_args
from webnotes.model.bean import getlist
import os, string, random, re

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def on_update(self):
		self.create_new_site()
		if (os.path.exists(os.path.join(get_base_path(), "sites", self.doc.site_name))):
			self.update_global_defaults()
		webnotes.msgprint("Updated")

	def make_primary_sites_settings(self):
		# webnotes.errprint("tre")
		exec_in_shell("""mkdir {path}/sites """.format(path=get_base_path()))

		with open(os.path.join(get_base_path(), "conf.py"), "a") as conf_file:
			conf_file.write('\nsites_dir = "%s"' % ("{path}/sites".format(path=get_base_path())))


		exec_in_shell(""" mkdir -p {path}/sites/{site_name}/
			""".format(path=get_base_path(), site_name= self.doc.site_name))

		exec_in_shell(""" mv {path}/public {path}/sites/{site_name}/public
			""".format(path=get_base_path(), site_name= self.doc.site_name))
		

		with open("conf.py") as temp:
			lines = temp.readlines()
		
		db_name = lines[7][:-1].split('=')
		db_name = '"'+ db_name[0] + '" :'+ db_name[1].replace("'", '"') 
		
		db_password = lines[8][:-1].split('=')
		db_password = '"'+ db_password[0] + '" :'+ db_password[1].replace("'", '"')

		with open(os.path.join(get_base_path(), "site_config.json"), "w") as conf_file:
			conf_file.write("{\n"+db_name+",\n"+db_password+"\n}")

		exec_in_shell(""" mv {path}/site_config.json {path}/sites/{site_name}/
			""".format(path=get_base_path(), site_name= self.doc.site_name))


		exec_in_shell(""" ./lib/wnf.py --build """)

		self.update_nginx_conf()


	def update_nginx_conf(self):
		nginx_conf = """
user www-data www-data;
worker_processes 1;
pid /run/nginx.pid;

events {
        worker_connections 1024;
        accept_mutex off;
        # multi_accept on;
}

http {

        ##
        # Basic Settings
        ##
        include mime.types;

        access_log /tmp/nginx.access.log combined;
        types_hash_max_size 2048;
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 65;
        # server_tokens off;

        # server_names_hash_bucket_size 64;
        # server_name_in_redirect off;

        include /etc/nginx/mime.types;
        default_type application/octet-stream;

        upstream erpnext {
                server 127.0.0.1:8000 fail_timeout=0;
        }
        ##
        # Logging Settings
        ##

        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;

        ##
        # Gzip Settings
        ##

        gzip on;
        gzip_disable "msie6";

        # gzip_vary on;
        # gzip_proxied any;
        # gzip_comp_level 6;
        # gzip_buffers 16 8k;
        # gzip_http_version 1.1;
        # gzip_types text/plain text/css application/json application/x-javascript text/xml application/xml application/xml+rss text/javascript;

        ##
        # nginx-naxsi config
        ##
        # Uncomment it if you installed nginx-naxsi
        ##

        #include /etc/nginx/naxsi_core.rules;

        ##
        # nginx-passenger config
        ##
        # Uncomment it if you installed nginx-passenger
        ##

        #passenger_root /usr;
        #passenger_ruby /usr/bin/ruby;

        ##
        # Virtual Host Configs
        ##
        server {
        	listen 80 default;
                client_max_body_size 4G;
                server_name localhost;
                keepalive_timeout 5;
                sendfile on;
                root %s/sites;

                location /private/ {
                        internal;
                        try_files /$uri =424;
                }

                location / {
                        try_files /public/$uri @magic;
                }

                location @magic {
                    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                    proxy_set_header X-Use-X-Accel-Redirect True;
                    proxy_set_header Host $http_host;
                    proxy_read_timeout 120;
                    proxy_redirect off;
                    proxy_pass  http://erpnext;
                }
        }
        include /etc/nginx/conf.d/*.conf;
        include /etc/nginx/sites-enabled/*;
}


#mail {
#       # See sample authentication script at:
#       # http://wiki.nginx.org/ImapAuthenticateWithApachePhpScript
#
#       # auth_http localhost/auth.php;
#       # pop3_capabilities "TOP" "USER";
#       # imap_capabilities "IMAP4rev1" "UIDPLUS";
#
#       server {
#               listen     localhost:110;
#               protocol   pop3;
#               proxy      on;
#       }
#
#       server {
#               listen     localhost:143;
#               protocol   imap;
#               proxy      on;
#       }
#}

		"""%(get_base_path())

		with open(os.path.join(get_base_path(), "nginx.conf"), "w") as conf_file:
			conf_file.write(nginx_conf)

		exec_in_shell(""" echo MedSynaptic | sudo -S mv {path}/nginx.conf /etc/nginx/
			""".format(path=get_base_path(), site_name= self.doc.site_name))

	def create_new_site(self):
		root_password = webnotes.conn.get_value("Global Defaults", None, "root_password")
		self.initiate_tenant_ctreation(root_password, self.doc.site_name, True)
		
		for row in getlist(self.doclist, 'sub_tenant'):
			self.initiate_tenant_ctreation(root_password, row.sub_tenant_url)	

	def initiate_tenant_ctreation(self, root_password, site_name, is_parent=False):

		exec_in_shell("""{path}/lib/wnf.py --install {dbname} --root-password {root_password} --site {name}
			""".format(path=get_base_path(), dbname=site_name[:16].replace('.', '_'), root_password=root_password, name=site_name))

		self.add_to_hosts(site_name)

		exec_in_shell("{path}/lib/wnf.py --build".format(path=get_base_path()))

		if is_parent:
			self.update_db_name_pwd()
		else:
			self.update_child_details(site_name)

	def add_to_hosts(self, site_name):
		webnotes.errprint("host")
		with open('/etc/hosts', 'rt') as f:
			s = f.read() + '\n' + '127.0.0.1\t\t\t %s \n'%site_name
			with open('hosts', 'wt') as outf:
				outf.write(s)

		os.system('echo MedSynaptic | sudo -S mv {path}/hosts /etc/hosts'.format(path=get_base_path()))

	def update_db_name_pwd(self):
		with open (get_base_path()+'/sites/'+self.doc.site_name+'/site_config.json', 'r') as site_config:
			lines = site_config.readlines()

		db_name = lines[1].split(':')[1].replace('"','')[:-3]
		db_pwd = lines[2].split(':')[1].replace('"','')[:-1]
		webnotes.conn.sql("update `tabSite Details` set database_name = LTRIM('%s'), database_password = LTRIM('%s') where name = '%s' "%(db_name, db_pwd, self.doc.name), debug=1)
		webnotes.conn.sql("commit")

	def update_child_details(self, sub_tenant_url):
		with open (get_base_path()+'/sites/'+sub_tenant_url+'/site_config.json', 'r') as site_config:
			lines = site_config.readlines()

		db_name = lines[1].split(':')[1].replace('"','')[:-3]
		db_pwd = lines[2].split(':')[1].replace('"','')[:-1]
		webnotes.conn.sql("update `tabSub Tenant Details` set db = LTRIM('%s'), pwd = LTRIM('%s') where sub_tenant_url = '%s' "%(db_name, db_pwd, sub_tenant_url), debug=1)
		webnotes.conn.sql("commit")

	def update_global_defaults(self):
		site_details = webnotes.conn.sql("select database_name, database_password from `tabSite Details` where name = '%s'"%(self.doc.name))
		if site_details:
			import MySQLdb
			myDB = MySQLdb.connect(user="%s"%site_details[0][0], passwd="%s"%site_details[0][1], db="%s"%site_details[0][0])
			cHandler = myDB.cursor()
			cHandler.execute("update  tabSingles set value = '%s' where field='is_active' and doctype = 'Global Defaults'"%self.doc.is_active)
			cHandler.execute("commit")

@webnotes.whitelist(allow_guest=True)
def get_installation_note(site_name ,_type='POST'):
	# from webnotes.model.doc import Document
	webnotes.bean({
			"doctype":"Site Details",
			"site_name": site_name,
			"is_active":"1"
		}).insert()
	# http://saurabh.erp.com:8000/server.py?cmd=core.doctype.site_details.site_details.get_installation_note&site_name=rohit3.erp.com&_type='POST'

@webnotes.whitelist(allow_guest=True)
def activate_deactivate(site_name , is_active, _type='POST'):
	site_details = webnotes.conn.sql("select database_name, database_password from `tabSite Details` where name = '%s'"%(site_name))
	if site_details:
		import MySQLdb
		myDB = MySQLdb.connect(user="%s"%site_details[0][0], passwd="%s"%site_details[0][1], db="%s"%site_details[0][0])
		cHandler = myDB.cursor()
		cHandler.execute("update  tabSingles set value = '%s' where field='is_active' and doctype = 'Global Defaults'"%is_active)
		cHandler.execute("commit")

@webnotes.whitelist(allow_guest=True)
def get_installation_note1(_type='POST'):
	from httplib2 import Http
	h = Http()
	webnotes.errprint([h.request])

def create_site():
	from webnotes.model.code import get_obj
	webnotes.errprint('test')
	sites = webnotes.conn.sql("""select name from `tabSite Details` where flag = 'False' """,as_list=1)
	# webnotes.errprint(sites)
	for site in sites:

		"""For Primary site creation, checks site path exist or not"""
		if not (os.path.exists(os.path.join(get_base_path(), "sites"))):
			get_obj('Site Details', site[0]).make_primary_sites_settings()

		"""For secondary sites"""
		if not (os.path.exists(os.path.join(get_base_path(), "sites", site[0]))):
			get_obj('Site Details', site[0]).create_new_site()
			# webnotes.conn.sql("""update `tabSite Details` set flag = 'True' where name = '%s' """%(site[0]),as_list=1)	