#cooker
#Authors: Kheshav Sewnundun <kheshavsewnundun@gmail.com>
#Creation: 04-Jan-2016
#License: BSD

from threading import Thread
import os, re, tempfile, sys, time, string
import fabric , fabric.operations, fabric.context_managers
import ansible
from fabric.api import *
from fabric.contrib.files import *


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

	def run(self,command):
		with settings(warn_only=True):
			if (self.getMode() is "local"):
				return local(command,True)
			if self.isSudo():
				return sudo(command,pty=False)
			return run(command,pty=False)

	# ============================
	#
	# Repository functions
	#=============================

	def package_ensure(self,*args):
		'''Package ensure dispatcher'''
		def func_not_found(): 
        		print "No Function " + self.i + " Found!"
		for package in args:
			func_name = self.getPackage() + "_package_ensure"
			func = getattr(self,func_name,func_not_found)
			func(package)

	def update(self):
		'''Update dispatcher'''
		def func_not_found(): 
        		print "No Function " + self.i + " Found!"
		func_name = self.getPackage() + "_update"
		func = getattr(self,func_name,func_not_found)
		func()

	def apt_package_ensure(self,package):
		if (self.getMode() is "local"):
			return local("apt-get install -y %s" % package )
		if self.isSudo():
			return sudo("apt-get install -y %s" % package)
		return run("apt-get install -y %s" % package)

	def apt_update(self):
		return self.run("apt-get -y update")

	def yum_package_ensure(self,package):
		'''Install Package using yum'''
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

	def yum_update(self):
		'''Updates the OS'''
		return self.run("yum -y update")

	# ========================
	#
	# OS Utilities
	#=========================

	def copy(self,source=None,destination=None,recursive=None):
		'''Copy file from one destination to another'''
		if (source is None) or (destination is None):
			fabric.utils.abort("Source and Destination must be specified")
		if recursive is None:
			self.run("cp %s %s" % (source,destination))
		else:
			self.run("cp -r %s %s" % (source,destination))

	def move(self,source=None,destination=None):
		'''Move file from one destination to the other'''
		if (source is None) or (destination is None):
			fabric.utils.abort("Source and Destination must be specified")
		self.run("mv %s %s" % (source,destination))

	def fileIso(self,file1,file2):
		'''Check if two files are iso'''
		cmd = "openssl dgst -md5 %s|awk '{print $2}'"
		file1 = self.run(cmd  % (file1))
		file2 = self.run(cmd % (file2))
		if file1 == file2:
			return True
		return False

	def createUser(self,user,password = None,home = None,shell = None,group = None,createHome = True ):
		'''Create new user'''
		if(self.file_Contains("/etc/passwd",user,False)):
			warn("User %s already exists!!!" % user)
			return False
		options = []
		if home:
			options.append(" -d %s" % (home))
		if shell:
			options.append(" -s %s" % (shell))
		if group:
			options.append(" -g %s" % (group))
		if createHome:
			options.append(" -m")
		result = self.run("useradd %s %s" % (user,"".join(options)))
		if password:
			if result.return_code == 0:
				password = local("openssl passwd %s" % (password),True)
				self.run("usermod -p %s %s" % (password,user))

	def deleteUser(self,user = None,uid=None,deleteHome = False):
		'''Delete User'''
		options = []
		if deleteHome:
			options.append(" -r")
		if user:
			codeReturn = self.run("userdel %s %s" % ("".join(options),user))
			if codeReturn == 0:
				return True
			return False
		elif uid:
			user = self.run("getent passwd %s| cut -d: -f1 |grep ''" % (uid))
			if (user.return_code != 0):
				return False
			self.deleteUser(user,deleteHome=deleteHome)


	# ========================
	#
	# Directory Utilities
	#=========================

	def dir_ensure(self,destination = None , user =None,group = None, permissions =None,recursive= False):
		'''Ensures a directory is created'''
		if (destination is None):
			warn("Destination of directory must be specified")
			return False
		if (self.dir_exists(destination)):
			warn("Destination folder already exists; Just setting permissions")
			self.dir_setAttr(destination,user,group,permissions,recursive)
		else:
			self.run("mkdir -p %s" % (destination))
			self.dir_setAttr(destination,user,group,permissions,recursive)

	def dir_exists(self,directory):
		'''Check if directory exists'''
		if ((self.run("test -d %s" % (directory))).return_code == 0):
			return True
		else:
			warn("Directory doesnot exists")
			return False

	

	def dir_getGroup(self,directory,octal = False):
		'''Get group of the directory'''
		if(self.dir_exists(directory)):
			argument = octal and '%g' or '%G'
			return self.run("stat -c %s %s" % (argument,directory))

	def dir_getHash(self,directory,algorithm="md5",sum=False):
		'''Get hash of files in directory'''
		SupportedAlgorithm = ["md5","sha256","sha512"]
		assert algorithm in SupportedAlgorithm, "Algorithm must be one of: %s" % (SupportedAlgorithm)
		if(self.dir_exists(directory)):
			if not sum:
				puts("Please be patient the command might take some time")
				return self.run("find %s -type f -print0 | xargs -0 openssl dgst -%s" % (directory,algorithm))
			else:
				return self.run("cmd=`find %s -type f -print0 | xargs -0 openssl dgst -%s` && echo $cmd | openssl dgst -%s |cut -d = -f2" % (directory,algorithm,algorithm))

	
	def dir_getMount(self,directory):
		'''Get the mounting point of the directory'''
		if(self.dir_exists(directory)):
			return self.run("df -P %s | awk '{c++} c==2 {print $NF}'" % (directory))

	def dir_getOwner(self,diretory,octal=False):
		'''Get Owner of the directory'''
		if(self.dir_exists(directory)):
			argument = octal and '%u' or '%U'
			return self.run("stat -c %s %s" % (argument,directory))

	def dir_getPermission(self,directory,hexa = False):
		'''Get permission of a directory'''
		if(self.dir_exists(directory)):
			argument = hexa and '%a' or '%A'
			return self.run("stat -c %s %s" % (argument,directory))

	def dir_getRunningProcess(self,directory):
		'''Return array of users using the directory'''
		if(self.dir_exists(directory)):
			return string.split(self.run("lsof %s |awk '{print $3}' |sort|uniq |grep -iv USER" % (directory)))


	def dir_list(self,directory,options=None):
		'''list directory'''
		if(self.dir_exists(directory)):
			options = options and "-"+options or ""
			return self.run("ls %s %s" % (options,directory))
		else:
			warn("Directory doesnot exists")
			return False


	def dir_setAttr(self,location = None,user = None,group=None,permissions = None,recursive = False):
		'''Set directory permissions'''
		if recursive:
			recursive = " -R"
		else:
			recursive = ""
		if group:
			self.run("chgrp %s %s %s" % (recursive,group,location))
		if permissions:
			self.run("chmod %s %s %s" % (recursive,permissions,location))
		if user:
			self.run("chown %s %s %s" % (recursive,user,location))


	def dir_remove(self,directory,recursive = False):
		'''Remove a directory'''
		if(self.dir_exists(directory)):
			argument = ""
			if recursive:
				argument = "r"
			self.run("rm -%sf %s && echo 'Directory %s removed' " % (argument,directory,directory))
		else:
			warn("Directory doesnot exists")
	
	
	# ========================
	#
	# File Utilities
	#=========================

	def file_Contains(self,path,text,exact):
		'''Check if file contains the searched keywoord'''
		if (self.getMode() is "local"):
			result = local("grep %s %s" %(text,path),True)
			if result.return_code == 0:
				return True
			else:
				return False
		return fabric.contrib.files.contains(path,text,exact)

	def file_diff(self,files):
		'''Get difference between two files'''
		for file in files:
			if not self.file_exists(file):
				return False
		return self.run("diff -uNp %s %s" %(files[0],files[1]))

	def file_exists(self,file):
		'''Check if File exists'''
		if ((self.run("test -f %s" % (file))).return_code == 0):
			return True
		else:
			warn("File %s doesnot exists" % file)
			return False

	def file_setAttr(self,file =None,user = None,group=None,permissions = None):
		'''Set file permissions'''
		if(self.file_exists(file)):
			self.dir_setAttr(location = file,user = user,group=group,permissions = permissions,recursive = False)

	def file_getHash(self,files,algorithm="md5"):
		'''return Hash of files'''
		SupportedAlgorithm = ["md5","sha256","sha512"]
		assert algorithm in SupportedAlgorithm, "Algorithm must be one of: %s" % (SupportedAlgorithm)
		Hashes = {}
		if isinstance(files,list):
			for file in files:
				if self.file_exists(file):
					hash = self.run("openssl dgst -%s %s |cut -d = -f2" % (algorithm,file)).strip()
					Hashes[file] = hash
				else:
					Hashes[file] = None
		elif isinstance(files,str):
			if self.file_exists(files):
				hash = self.run("openssl dgst -%s %s |cut -d = -f2" % (algorithm,files)).strip()
				Hashes[files] = hash
			else:
				Hashes[files] = None
		return Hashes

	# ========================
	#
	# Process Utilities
	#=========================

	def process_find(self,process,exact=True):
		'''Find the process and return the user an array
		of PD of the matched process'''
		options = exact and "-w" or ""
		PROCESS = {}
		if isinstance(process,list):
			for p in process:
				processes  = self.run("ps -A |grep %s %s |awk '{print $1}'" % (options,p))
				pids = []
				for pid in processes.splitlines():
					pids.append(pid)
				PROCESS[p] = pids
		elif isinstance(process,str):
			pids = []
			for pid in self.run("ps -A |grep %s %s |awk '{print $1}'" % (options,process)).splitlines():
				pids.append(pid)
			PROCESS[process] = pids
		return PROCESS

	def process_killByName(self,process):
		'''Kill a process by its name'''
		PROCESS = self.process_find(process)
		for p in PROCESS[process]:
			self.run("kill -9 %s" % p)

	def process_sendSignal(self,process,signal):
		'''Sends signal to a process'''
		PROCESS = self.process_find(process)
		for p in PROCESS[process]:
			self.run("kill -%s %s"%(signal,p))

	def process_swapValue(self,process):
		'''return the process Swap value'''
		swaps = {}
		if isinstance(process,str):
			ProcessList = []
			PROCESS = self.process_find(process)
			swap = {}
			for p in PROCESS[process]:
				swap[p] = self.run("cat /proc/%s/status |awk '/VmSwap|Name/{printf $2 \" \" $3}END{ print \"\"}' |awk '{print $2 \" \" $3}'" %(p))
				swaps[process] = swap
			ProcessList.append(swaps)
			return ProcessList
		elif isinstance(process,list):
			ProcessList = []
			for p in process:
				PROCESS = self.process_find(p)
				for p in PROCESS:
					result = self.process_swapValue(p)
					if(result):
						ProcessList.append(result)
			return ProcessList