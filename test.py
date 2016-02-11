from cooker import *

myCooker = cooker("local",True)
#env.hosts=['127.0.0.1']
myCooker.setPackage("yum")
myCooker.connect("127.0.0.1")
#print myCooker.getMode()
#myCooker.dir_ensure("/tmp/tototoot",user="k.sewnundun",group="k.sewnundun",permissions="777",recursive=True)
#myCooker.dir_remove("/tmp/tototoot",True)
#print myCooker.file_diff(["/root/a.php","/root/c.php"])
#print myCooker.dir_getHash("/tmp",algorithm="md5")
#print myCooker.process_find(["httpd","udevd"])
#print myCooker.process_find("httpd")
#myCooker.process_killByName("rotatelogs")
#myCooker.test()
#myCooker.process_sendSignal("httpd","9")
#print myCooker.process_swapValue("httpd")
print myCooker.process_swapValue(["httpd","mingetty","toto"])