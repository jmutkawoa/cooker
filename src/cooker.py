#cooker
#Authors: Kheshav Sewnundun <kheshavsewnundun@gmail.com>
#Creation: 04-Jan-2016
#License: BSD

from threading import Thread
import os, re, tempfile, sys, time
import fabric , fabric.operations, fabric.context_managers
import ansible
from fabric.api import *


class cooker:
	DEFAULT_PACKAGE = "apt"
	DEFAULT_ACTION	= "local"
	SUDO			= False
	PASS 			= False
	KEY             = False
	OPTIONS = dict(
		package  = ["apt","yum"],
		logging	 = ["y","n"],
		action 	 = ["local", "remote"]
	)
	
	def __init__(self,action = None,warn_only = True ):
		if not (action is None):
			self.DEFAULT_ACTION = action
			warn("%s Mode selected" % (action)) 
		else:
			assert action in self.OPTIONS['action'], "action must be one of: %s" % (self.OPTIONS['action'])
		env.host_string = "127.0.0.1"
		env.warn_only = warn_only
	def isSudo(self):
		return self.SUDO

	def setMode(self,mode):
		self.DEFAULT_ACTION = mode

	def getMode(self):
		return self.DEFAULT_ACTION

	def connect(self,host=None,user=None,keyFile=None):
		if (self.getMode() is "local"):
			warn("You are in local mode not need to connect")
		if (host is None):
			sys.stderr.write("\nFatal error: %s\n" % "Host undefined")
			sys.exit(1)
		else:
			env.host_string = host
		if not (user is None):
			self.user =  user
			env.user = user
		if not(keyFile is None):
			env.key_filename = keyFile

	def setPackage(self,package=None):
		if not (package is None):
			assert package in self.OPTIONS['package'], "Package must be one of: %s" % (self.OPTIONS['package'])
			self.DEFAULT_PACKAGE = package

	def getPackage(self):
		return self.DEFAULT_PACKAGE

	# ============================
	#
	# Repository functions
	#=============================

	def package_ensure(self,*args):
		def func_not_found(): 
        		print "No Function " + self.i + " Found!"
		for package in args:
			func_name = self.getPackage() + "_package_ensure"
			func = getattr(self,func_name,func_not_found)
			func(package)

	def apt_package_ensure(self,package):
		if (self.getMode() is "local"):
			return local("apt-get install -y %s" % package )
		if self.isSudo():
			return sudo("apt-get install -y %s" % package)
		return run("apt-get install -y %s" % package)

	def yum_package_ensure(self,package):
		if (self.getMode() is "local"):
			status = local("yum install -y %s" % package,True)
		elif (self.isSudo()):
			status = sudo("yum install -y %s" % package)
		else:
			status = run("yum install -y %s" % package)

		if "Complete" in status:
			puts("Package %s installed" % package)
			return True
		else:
			warn("Package %s not installed" % package)
			return False

