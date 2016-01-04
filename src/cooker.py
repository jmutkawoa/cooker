#cooker
#Authors: Kheshav Sewnundun <kheshavsewnundun@gmail.com>
#Creation: 04-Jan-2016
#License: BSD

from threading import Thread
import os, re, tempfile, sys, time
import fabric
import ansible

DEFAULT_PACKAGE = "apt"
DEFAULT_ACTION	= "local"
OPTIONS = dict(
	package  = ["apt","yum"],
	logging	 = ["y","n"],
)

class cooker:
	def __init__(self,action = DEFAULT_ACTION ):
		