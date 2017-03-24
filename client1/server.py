import socket
import threading
import os
from socket import *
from threading import Thread
from commands import *
import time
import sys
import signal
s = socket(AF_INET,SOCK_STREAM)
s.setsockopt(SOL_SOCKET,SO_REUSEADDR, 1)
u = socket(AF_INET,SOCK_DGRAM)
u.setsockopt(SOL_SOCKET,SO_REUSEADDR, 1)
host = gethostname()
server_address1 = (host,20000)
server_address = (host,20001)
u.bind(server_address1)
port = 1137
port1 = 1138
updatetime=0
c=''
s.bind((host,port))	
s.listen(5)
c, addr = s.accept()
def commandthread():
	updatetime=0
	while True:
		time.sleep(3)
		if updatetime==0 :
			print 'Checking if files need to be updated'
			c.send('8')
			time.sleep(0.5)

		command=(raw_input('\n\n')).split()

		if command[0] == "q" :
			c.send('100')
			time.sleep(2)
			s.close()
			u.close()
			print 'BYE\n'
			os._exit(0)

		updatetime=(updatetime+1)%1000;
		if len(command) > 1 :
			if command[0]=="a" :
				c.send("Hello")
				filename=raw_input('Enter Filename :')
				fsend(filename)

			elif command[0]=="index":
				if command[1]=="longlist" :
					c.send('1')
				elif command[1]=="shortlist":
					c.send('2')
					m=command[2] + ' ' + command[3]
					time.sleep(0.5)
					c.send(m)
				elif command[1]=="regex" :	
					c.send('3')
					time.sleep(0.5)
					c.send(command[2])
				else :
					print 'Unknown Flag'

			elif command[0]=="hash" :
				if command[1]=="verify":
					c.send('4')
					time.sleep(0.5)
					c.send(command[2])

				elif command[1]=="checkall":
					c.send('5')
				else :
					print 'Unknown Flag'

			elif command[0]=="download":
				if command[1]=="TCP":
					udpflag=0
					c.send('6')
					time.sleep(0.5)
					c.send(command[2])

				elif command[1]=="UDP":
					c.send('7')
					time.sleep(0.5)
					c.send(command[2])

				else :
					print 'Unknown Flag'
          

def datathread():
	while True:
		data=c.recv(1024)
		print data
		if data=='66':
			fileinfo=(c.recv(1024))
			fileinfo=fileinfo.split()
			print fileinfo
			print 'Filename:       ' + fileinfo[0]
			print 'Filesize:       ' + fileinfo[1]
			print 'FileTimestamp:  ' + fileinfo[2]
			frecieve(fileinfo[6],fileinfo[0],fileinfo[5])
		
		elif data=='100':
			s.close()
			u.close()
			print 'BYE\n'
			os._exit(0)

		elif data=='8':
			status,filelist = getstatusoutput('ls')
			filelist=filelist.split()
			final = ''
			for i in range(len(filelist)):
				cmd1 = 'md5sum ' + filelist[i]
				cmd2 = """ stat --printf="%Y"  """ + filelist[i]
				status,o1 = getstatusoutput(cmd1)
				status,o2 = getstatusoutput(cmd2)
				final = final + o1 + ' ' + o2 + ' '
			c.send('88')
			time.sleep(0.5)
			c.send(final)

		elif data=='88' :
			print 'Getting remote filelist'
			oldfiles = []
			totalfileinfo = c.recv(1024)
			totalfileinfo = totalfileinfo.split()
			status,myfilelist = getstatusoutput('ls')
			myfilelist=myfilelist.split()
			for i in range(len(totalfileinfo)) :
				if i%3==1 and totalfileinfo[i] in myfilelist :
					print 'CheckinG File : '  + totalfileinfo[i]
					status,currhash = getstatusoutput('md5sum ' + totalfileinfo[i])
					status,currtime = getstatusoutput(""" stat --printf="%Y" """ + totalfileinfo[i])
					currtime=(currtime.split())[0]
					if currhash != totalfileinfo[i-1] and currtime < totalfileinfo[i+1] :
						oldfiles.append(totalfileinfo[i])
			if len(oldfiles) > 0 :
				print 'Files To Be Downloaded : ' , oldfiles
				print 'Starting Download Process'
				for i in range(len(oldfiles)):
					c.send('6')
					time.sleep(0.5)
					c.send(oldfiles[i])
					newdata=c.recv(1024)
					while newdata == '' :
						pass
					if newdata == '66' :
						fileinfo=(c.recv(1024))
						fileinfo=fileinfo.split()
						print 'Filename:       ' + fileinfo[0]
						print 'Filesize:       ' + fileinfo[1]
						print 'FileTimestamp:  ' + fileinfo[2]
						frecieve(fileinfo[6],fileinfo[0],fileinfo[5])
						print 'File Received : ' ,  oldfiles[i]

			else :
				print 'No Need to Download any files'

		elif data=='9':
			status,output=getstatusoutput('ls')
			c.send('99')
			time.sleep(0.5)
			c.send(output)

		elif data=='20':
			filename = c.recv(1024)
			c.send('6')
			time.sleep(0.5)
			c.send(filename)

		elif data=='11':
			filename = c.recv(1024)
			print filename
			cmd1 = 'md5sum ' + filename
			cmd2 = """ stat --printf="%Y" """ + filename
			status,o1 = getstatusoutput(cmd1)
			status,o2 = getstatusoutput(cmd2)
			final = o1 + ' ' + o2
			c.send('111')
			time.sleep(0.5)
			c.send(final)

		elif data=='6':
			filename=c.recv(1024)
			cmd1='md5sum ' + filename
			cmd=""" stat --printf="%n \t %s \t %y \t %a" """ + filename
			status,text= getstatusoutput(cmd)
			status1,text1 = getstatusoutput(cmd1)
			c.send('66');
			time.sleep(0.5)
			c.send(text + '\t' +text1)
			time.sleep(0.5)
			fsend(filename)

		elif data=='77':
			udpflag=c.recv(1024)
			udpflag=udpflag.split()
			downloadedhash = udpflag[1]
			print udpflag
			with open(udpflag[0], 'wb') as f:
				msg1=''
				while True:
					msg,server = u.recvfrom(1024)
					if msg == 'done' :
						break
					f.write(msg)
					print 'writing'
			f.close()
			print 'matching file hash'
			cmd = 'md5sum ' + udpflag[0]
			status,output = getstatusoutput(cmd)
			output=output.split()
			if output[0] == downloadedhash :
				print 'file received successfully[hashes match]'
				status,output = getstatusoutput('chmod ' + udpflag[2] + ' ' + udpflag[0])

			else :
				print 'file transfer error[hashes dont match]'

		elif data=='7':
			filename=c.recv(1024)
			time.sleep(0.5)
			c.send('77')
			time.sleep(0.5)
			cmd = 'md5sum ' + filename
			cmd1 = """ stat --printf="%a"  """ + filename
			status,output = getstatusoutput(cmd)
			status,output1 = getstatusoutput(cmd1)
			output=output.split()
			c.send(filename + ' ' + output[0] + ' ' + output1)
			f = open(filename,'rb')
			l = f.read(1024)
			while (l):
				u.sendto(l,server_address)
				print 'sending'
				l = f.read(1024)
			f.close()
			u.sendto('done',server_address)
			print 'file sending complete'


		elif data=='1':
			cmd='stat --printf="%n \n %s \n %F \n %y \n\n" * '
			status, text = getstatusoutput(cmd)
			c.send(text)
			data=''

		elif data=='2':
			times=(c.recv(1024)).split()
			cmd = """ stat --printf="%Y %s  %F %n \n" * | awk  ' $1 >= """ + times[0] + """ && $1 <= """ + times[1] + """ { print $1 " " $2 " " $3 " " $4 " " } ' """ 
			status,text =  getstatusoutput(cmd)
			c.send(text)

		elif data=='3':
			com=c.recv(1024)
			cmd = """stat --printf="%n \t %s \t %F \t %y \n" * | grep""" + ' ' + com
			status,text =  getstatusoutput(cmd)
			if status!= 0 :
				c.send('command could not be executed')
			else :
				c.send(text)
	
		elif data=='4':
			com=c.recv(1024)	
			cmd1 = 'md5sum '+ com
			cmd2 = """ stat --printf="%y"  """ + com 
			status1,text1 = getstatusoutput(cmd1)
			status2,text2 = getstatusoutput(cmd2)
			if status1!=0 or status2!=0 :
				c.send('could not execute command')
			else :
				c.send(text1 + '   ' + text2)

		elif data=='5':
			status1,text1= getstatusoutput('ls')
			files=text1.split()
			final=''
			for i in range(len(files)) :
				if oc.path.isfile(files[i]) :
					com = files[i]
					cmd1 = 'md5sum '+ com
					cmd2 = """ stat --printf="%y"  """ + com 
					status2,text2 = getstatusoutput(cmd1)
					status3,text3 = getstatusoutput(cmd2)
					final = final + text2 + '   ' + text3 + '\n'
			c.send(final)

		
def main():
	print 'Got connection from', addr
	Thread(target = commandthread).start()
	Thread(target = datathread).start()



def fsend(filename) :
	f = open(filename,'rb')
	l = f.read(1024)
	while (l):
		c.send(l)
		l = f.read(1024)
	f.close()
	print 'file sent'
	time.sleep(0.5)
	c.send("done")


def frecieve(downloadedhash,filename,filepermissions) :
	with open(filename, 'wb') as f:
		print 'file opened'
		while True:
			print('receiving data...')
			data = c.recv(1024)
			if data == "done":
				break
			f.write(data)
	f.close()
	print 'file recieved'
	print 'checking if file hashes match'
	cmd='md5sum ' + filename
	status,output = getstatusoutput(cmd)
	output=output.split()
	if downloadedhash == output[0] :
		print 'Hashes Matched'
		status,output = getstatusoutput('chmod ' + filepermissions + ' ' + filename)
	else :
		print 'Hashes Do Not Match'

if __name__== "__main__" :
	main()