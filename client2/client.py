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
server_address1 = (host,20001)
server_address = (host,20000)
u.bind(server_address1)
port = 1138
port1 = 1137
updatetime=0	
def commandthread():
	updatetime=0
	while True:
		time.sleep(3)
		if updatetime==500 :
			print 'Checking if files need to be updated'
			c.send('8')
			time.sleep(0.5)
		command=raw_input('\n\n').split()
	
		if command[0] == "quit" :
			s.send('100')	
			time.sleep(0.5)
			s.close()
			u.close()
			print 'BYE\n'
			os._exit(0)
	
		updatetime=(updatetime+1)%1000
		
		if len(command) > 1 :
			if command[0]=="a" :
				s.send("Hello")
				filename=raw_input('Enter Filename :')
				fsend(filename)

			elif command[0]=="index":
				if command[1]=="longlist" :
					s.send('1')
				elif command[1]=="shortlist":
					s.send('2')
					m=command[2] + ' ' + command[3]
					time.sleep(0.5)
					s.send(m)
				elif command[1]=="regex" :
					s.send('3')
					time.sleep(0.5)
					s.send(command[2])
				else :
					print 'Unknown Flag'

			elif command[0]=="hash" :
				if command[1]=="verify":
					s.send('4')
					time.sleep(0.5)
					s.send(command[2])

				elif command[1]=="checkall":
					s.send('5')
				else :
					print 'Unknown Flag'

			elif command[0]=="download":
				if command[1]=="TCP":
					udpflag=0
					s.send('6')
					time.sleep(0.5)
					s.send(command[2])

				elif command[1]=="UDP":
					s.send('7')
					time.sleep(0.5)
					s.send(command[2])

				else :
					print 'Unknown Flag'
          
		else :
			print 'Invalid Command'


def datathread():
	while True:
		data=s.recv(1024)
		if  not data in range(200):
			print data
		if data=='66':
			fileinfo=(s.recv(1024))
			fileinfo=fileinfo.split()
			print 'Filename:       ' + fileinfo[0]
			print 'Filesize:       ' + fileinfo[1]
			print 'FileTimestamp:  ' + fileinfo[2]
			frecieve(fileinfo[5],fileinfo[0])
		

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
			s.send('88')
			time.sleep(0.5)
			s.send(final)

		elif data=='88' :
			print 'Getting remote filelist'
			oldfiles = []
			totalfileinfo = s.recv(1024)
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
			print 'Files To Be Downloaded : ' , oldfiles
			print 'Starting Download Process'
			for i in range(len(oldfiles)):
				s.send('6')
				time.sleep(0.5)
				s.send(oldfiles[i])
				newdata=s.recv(1024)
				while newdata == '' :
					pass
				if newdata == '66' :
					fileinfo=(s.recv(1024))
					fileinfo=fileinfo.split()
					print 'Filename:       ' + fileinfo[0]
					print 'Filesize:       ' + fileinfo[1]
					print 'FileTimestamp:  ' + fileinfo[2]
					frecieve(fileinfo[5],fileinfo[0])
					print 'File Received : ' ,  oldfiles[i]

		elif data=='6':
			filename=s.recv(1024)
			if os.path.isfile(filename) :
				cmd1='md5sum ' + filename
				cmd=""" stat --printf="%n \t %s \t %y \t %a" """ + filename
				status,text = getstatusoutput(cmd)
				status1,text1 = getstatusoutput(cmd1)
				s.send('66');
				time.sleep(0.5)
				s.send(text + '\t' +text1)
				time.sleep(0.5)
				fsend(filename)


		elif data=='77':
			udpflag=s.recv(1024)
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
			filename=s.recv(1024)
			time.sleep(0.5)
			s.send('77')
			cmd = 'md5sum ' + filename
			cmd1 = """ stat --printf="%a"  """ + filename
			status,output = getstatusoutput(cmd)
			status,output1 = getstatusoutput(cmd1)
			if status == 0 :
				output=output.split()
				s.send(filename + ' ' + output[0] + ' ' + output1)
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
			s.send(text)
			data=''

		elif data=='2':
			times=(s.recv(1024)).split()
			cmd = """ stat --printf="%Y %s  %F %n \n" * | awk  ' $1 >= """ + times[0] + """ && $1 <= """ + times[1] + """ { print $1 " " $2 " " $3 " " $4 " " } ' """ 
			status,text =  getstatusoutput(cmd)
			s.send(text)

		elif data=='3':
			com=s.recv(1024)
			cmd = """stat --printf="%n \t %s \t %F \t %y \n" * | grep""" + ' ' + com
			status,text =  getstatusoutput(cmd)
			if status!= 0 :
				s.send('command could not be executed')
			else :
				s.send(text)
	
		elif data=='4':
			com=s.recv(1024)	
			cmd1 = 'md5sum '+ com
			cmd2 = """ stat --printf="%y"  """ + com 
			status1,text1 = getstatusoutput(cmd1)
			status2,text2 = getstatusoutput(cmd2)
			if status1!=0 or status2!=0 :
				s.send('could not execute command')
			else :
				s.send(text1 + '   ' + text2)

		elif data=='5':
			status1,text1= getstatusoutput('ls')
			files=text1.split()
			final=''
			for i in range(len(files)) :
				if os.path.isfile(files[i]) :
					com = files[i]
					cmd1 = 'md5sum '+ com
					cmd2 = """ stat --printf="%y"  """ + com 
					status2,text2 = getstatusoutput(cmd1)
					status3,text3 = getstatusoutput(cmd2)
					final = final + text2 + '   ' + text3 + '\n'
			s.send(final)

		
def main():
	s.connect((host, port1))
	Thread(target = commandthread).start()
	Thread(target = datathread).start()



def fsend(filename) :
	f = open(filename,'rb')
	l = f.read(1024)
	while (l):
		s.send(l)
		l = f.read(1024)
	f.close()
	print 'file sent'
	time.sleep(0.5)
	s.send("done")


def frecieve(downloadedhash,filename) :
	with open(filename, 'wb') as f:
		print 'file opened'
		while True:
			print('receiving data...')
			data = s.recv(1024)
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
	else :
		print 'Hashes Do Not Match'

if __name__== "__main__" :
	main()