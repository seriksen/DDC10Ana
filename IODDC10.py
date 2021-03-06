import getpass
import telnetlib
import time
from datetime import date

class IODDC10:
	def __init__(self,HOST="192.168.1.3",nSam=8192,nEvs=10000,chMask='0x1',dataDir='/data/share/',password=None):
		self.HOST = HOST
		self.RFA = False
		self.nSam = nSam
		self.nEvs = nEvs
		self.chMask = chMask
		self.dataDir = dataDir
		self.tn = telnetlib.Telnet(self.HOST)
		print(self.tn.read_until(b'commands.',timeout=3).decode('ascii'))
		if password is None:
			self.password = getpass.getpass()
		else:
			self.password = password

	def setupDDC10(self,fade=5):
		self.tn.write(b"ls /mnt/share\n")
		pout = self.tn.read_eager().decode('ascii')
		pout += self.tn.read_until(b'root:/>',timeout=3).decode('ascii')
		if "No such file or directory" in pout:
			self.tn.write(b"mkdir -p /mnt/share\n")
			print("directory made")
			if self.password:
				print("mounting samba")
				self.tn.write(b"smbmount //192.168.1.100/SHARE /mnt/share -o username=lzer\n")
				print("waiting for pass prompt")
				pout = self.tn.read_eager().decode('ascii')
				pout += self.tn.read_until(b"Password: ",timeout=3).decode('ascii')
				while "Password:" not in pout:
					print('failed to get prompt!! RETRY')
					pout += self.tn.read_until(b"Password: ",timeout=3).decode('ascii')
				self.tn.write(self.password.encode('ascii') + b"\n")
				#self.tn.write(b"echo -------\n")
				passtst = self.tn.read_until(b"----",timeout=3).decode('ascii')
				if len(passtst)>len("----"):
					self.RFA = True
					print("Ready for Acquisition")
				else:
					print("SMB Failed somehow")
					print(passtst)
			else:
				print("Invalid password Set")

			self.tn.write(b"ls /mnt/share\n")
		else:
			print("smb mount dir already created")
			self.RFA = True
		cmd = "fadc_AD9648 {}".format(fade)
		self.tn.write(cmd.encode('ascii')+b'\n')
		#self.tn.write(b"echo -------\n")

		print(self.tn.read_until(b"----",timeout=3).decode('ascii'))
		self.tn.read_eager()

	def runAcq(self,outFile='data'):
		if self.RFA:
			print('running Acquisition')
			cmd = "time /mnt/share/binaries/DDC10_BinWaveCap_ChSel {0} {1} {2} /mnt/share/{3}.bin >> /mnt/share/{3}.log\n".format(self.chMask,self.nSam,self.nEvs,outFile)
			runStart = time.time()
			self.tn.write(cmd.encode('ascii'))
			print('waiting for run completion')
			print(self.tn.read_until(b"sys").decode('ascii'))
			print(self.tn.read_eager().decode('ascii'))
			with open(self.dataDir+outFile+".log",'a') as logfile:
				logfile.write(str(runStart)+"\n")
			print(self.tn.read_eager().decode('ascii'))
		else:
			print("Not Ready For Acquisition!!!!\nHAVE YOU RUN SETUP?\n")

	def loopAcq(self,nFiles=5,outDir='data'):
		if self.RFA:
			self.tn.write("mkdir -p /mnt/share/{}\n".format(outDir).encode('ascii'))
			self.tn.write("ls /mnt/share/{}\n".format(outDir).encode('ascii'))
			print(self.tn.read_until(b"----",timeout=3).decode('ascii'))
			print(self.tn.read_eager().decode('ascii'))
			for i in range(nFiles):
				self.runAcq("{0}/{1}".format(outDir,i))
				print("Completed file {}".format(i))
		else:
			print("Not Ready For Acquisition!!!!\nHAVE YOU RUN SETUP?\n")

def DoSingle(nSam,nEvs,chMask,OutName,password='123'):
	mDDC10 = IODDC10(nSam=nSam,nEvs=nEvs,chMask=chMask,password=password)
	mDDC10.setupDDC10()
	today = date.today()
	print('Date: {}'.format(today.strftime("%y%m%d")))
	mDDC10.runAcq(outFile="{0}_{1}_{2}_samples_{3}_events".format(OutName,today.strftime("%y%m%d"),nSam,nEvs))
	mDDC10.tn.close()

def DoMany(nSam,nEvs,chMask,nFiles,OutName,password='123'):
	mDDC10 = IODDC10(nSam=nSam,nEvs=nEvs,chMask=chMask,password=password)
	mDDC10.setupDDC10()
	today = date.today()
	print('Date: {}'.format(today.strftime("%y%m%d")))
	mDDC10.loopAcq(nFiles=nFiles,outDir="{0}_{1}_{2}_samples_{3}_events".format(OutName,today.strftime("%y%m%d"),nSam,nEvs))
	mDDC10.tn.close()

def RepMany(nSam,nEvs,chMask,nFiles,OutName,nRuns=2,dT=86000,password='123'):
	run=0
	while day<nRuns:
		DoMany(nSam,nEvs,chMask,nFiles,OutName,password)
		run += 1
		print('sleeping')
		time.sleep(dT)
