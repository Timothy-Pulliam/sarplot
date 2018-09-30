#!/usr/bin/env  python
import os
import getpass
from paramiko import client
from paramiko import AutoAddPolicy
import matplotlib.pyplot as plt
import pandas as pd
import tkinter as tk
import dateutil
import matplotlib.dates as md


def ssh(remote_host='', username='', password=''):

    ssh_client = client.SSHClient()
    ssh_client.load_system_host_keys()
    # Suppress "Server 'localhost' not found in known_hosts" errors by
    # auto adding unknown host keys (this is dangerous, Man in Middle)
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    ssh_client.connect(remote_host,
                       port=22,
                       username=username,
                       password=password,
                       allow_agent=False,
                       look_for_keys=False)
    # Generate Sar Data on remote host
    ssh_client.exec_command('sar -P ALL > /tmp/.sar_cpu.txt')
    ssh_client.exec_command('sar -b > /tmp/.sar_disk.txt')
    ssh_client.exec_command('sar -r > /tmp/.sar_mem.txt')
    # Pull sar data to local client
    ftp_get(ssh_client, '/tmp/.sar_cpu.txt', os.path.join(os.getcwd(), 'cpu.txt'))
    ftp_get(ssh_client, '/tmp/.sar_disk.txt', os.path.join(os.getcwd(), 'disk.txt'))
    ftp_get(ssh_client, '/tmp/.sar_mem.txt', os.path.join(os.getcwd(), 'mem.txt'))
    # Clean up after ourselves on remote host
    ssh_client.exec_command('rm -f /tmp/.sar_cpu.txt')
    ssh_client.exec_command('rm -f /tmp/.sar_disk.txt')
    ssh_client.exec_command('rm -f /tmp/.sar_mem.txt')
    ssh_client.close()


def ftp_get(ssh_client, remotefile, localfile):
    ftp_client = ssh_client.open_sftp()
    ftp_client.get(remotefile, localfile)
    ftp_client.close()


def plot(hostname):
    ## TODO
    ## Make sure data is plotted correctly
    ##
    cpu_data = pd.read_csv(os.path.join(os.getcwd(), 'cpu.txt'),
                           skiprows=[0], delim_whitespace=True, skipfooter=3,
                           engine='python')
    # We don't want to plot individual cores (yet), too much clutter                       
    cpu_data = cpu_data[cpu_data['CPU'] == 'all']
    disk_data = pd.read_csv(os.path.join(os.getcwd(), 'disk.txt'),
                            skiprows=[0], delim_whitespace=True, skipfooter=1)
    mem_data = pd.read_csv(os.path.join(os.getcwd(), 'mem.txt'),
                            skiprows=[0], delim_whitespace=True, skipfooter=1)
    dates = [dateutil.parser.parse(s) for s in cpu_data[cpu_data.columns[0]]]
                            
    # Sometimes, sar output contains the headers in the middle of the data
    # (to remind you of what the data is). We don't want this
    try:
        cpu_data = cpu_data[cpu_data['%user'] != '%user']
    except TypeError as e:
        pass
    try:
        disk_data = disk_data[disk_data['wtps'] != 'wtps']
    except TypeError as e:
        pass
    try:
        mem_data = mem_data[mem_data['kbmemfree'] != 'kbmemfree']
    except TypeError as e:
        pass    

    #cpu_data = cpu_data[['%user', '%nice', '%system', '%iowait', '%steal', '%idle']] = cpu_data[['%user', '%nice', '%system', '%iowait', '%steal', '%idle']].astype(float)
    # disk_data = disk_data[['tps', 'rtps', 'wtps', 'bread/s', 'bwrtn/s']] = disk_data[['tps', 'rtps', 'wtps', 'bread/s', 'bwrtn/s']].astype(float)
    # Convert data from string to float if necessary
    cpu_data = cpu_data.apply(pd.to_numeric, errors='ignore')
    disk_data = disk_data.apply(pd.to_numeric, errors='ignore')
    mem_data = mem_data.apply(pd.to_numeric, errors='ignore')
    
    # Please triple check that the legends match up to the coresponding lines
    # Plot cpu
    plt.figure(1)
    plt.subplots_adjust(bottom=0.2)
    plt.xticks( rotation=25 )
    ax=plt.gca()
    ax.xaxis_date()
    xfmt = md.DateFormatter('%H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    plt.title('CPU usage on host')
    lines = plt.plot(dates, cpu_data[cpu_data.columns[2:]])
    ax.legend(lines, [str(col) for col in list(cpu_data.columns[2:])])
    
    # Plot Disk I/O
    fig, axes = plt.subplots(2, sharex=True)
    fig.suptitle('Disk I/O on host')
    lines0 = axes[0].plot(dates, disk_data[disk_data.columns[1:4]])
    axes[0].legend(lines0, disk_data[disk_data.columns[1:4]])
    lines1 = axes[1].plot(dates, disk_data[disk_data.columns[4:]])
    axes[1].legend(lines1, disk_data[disk_data.columns[4:]])
    plt.subplots_adjust(bottom=0.2)
    plt.xticks( rotation=25 )
    ax=plt.gca()
    ax.xaxis_date()
    xfmt = md.DateFormatter('%H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    #plt.title('Disk I/O on host')
    #lines = plt.plot(dates, disk_data[disk_data.columns[1:]])
    #ax.legend(lines, [str(col) for col in list(disk_data.columns[1:])])
    
    # Plot Memory
    plt.figure(3)
    plt.subplots_adjust(bottom=0.2)
    plt.xticks( rotation=25 )
    ax=plt.gca()
    ax.xaxis_date()
    xfmt = md.DateFormatter('%H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    plt.title('Memory usage on host')
    lines = plt.plot(dates, mem_data[mem_data.columns[1:]])
    ax.legend(lines, [str(col) for col in list(mem_data.columns[2:])])
    plt.show()        
    
    
    # Graph the data
    # cpu_data.plot(title="CPU Usage on " + hostname)
    # plt.figtext(.02, .02, 'What does this mean?\nhttp://sebastien.godard.pagesperso-orange.fr/man_sar.html')
    # disk_data.plot(title="Disk Usage on " + hostname)
    # plt.figtext(.02, .02, 'What does this mean?\nhttp://sebastien.godard.pagesperso-orange.fr/man_sar.html')
    # mem_data.plot(title="Memory Usage on " + hostname)
    # plt.figtext(.02, .02, 'What does this mean?\nhttp://sebastien.godard.pagesperso-orange.fr/man_sar.html')
    # plt.show()


class Application(tk.Frame):
    '''This is the main GUI application for SarPlot. It is not necessary that
    you use the tkinter GUI to interact with SarPlot, it is just the most
    "user friendly" way'''
    def __init__(self, master=None):
        super().__init__(master)
        master.title("SarPlot")
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        
        self.master.bind('<Return>', self.submit)
        self.hostname_label = tk.Label(self, text="Hostname/IP")
        self.hostname_label.grid(row=0)
        self.hostname = tk.Entry(self)
        self.hostname.grid(row=0, column=1)
        self.username_label = tk.Label(self, text="username")
        self.username_label.grid(row=1)
        self.username = tk.Entry(self)
        self.username.grid(row=1, column=1)
        self.password_label = tk.Label(self, text="password")
        self.password_label.grid(row=2)
        self.password = tk.Entry(self, show="*", width=15)
        self.password.grid(row=2, column=1)
        self.submit = tk.Button(self, text="Submit", command=self.submit)
        self.submit.grid(row=4)

    def submit(self, event):
        hostname = self.hostname.get()
        username = self.username.get()
        password = self.password.get()
        ssh(hostname, username, password)
        plot(hostname)


if __name__ == '__main__':
    # TODO, try catch for incorrect hostnames/passwords
    # remote_host = input("Hostname or IP")
    # username = input("username for SSH")
    # password = getpass.getpass()

    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()

    # ssh(remote_host, username, password)
    # plot(remote_host)

    
    ## TODO
    ## Make better variable names
    ## Refactor plot()