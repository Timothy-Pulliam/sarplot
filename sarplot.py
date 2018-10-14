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


def ssh(remote_host='', username='', password='', command=''):

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
    ssh_client.exec_command(command)
    ssh_client.close()
    
    
def scp(remote_host='', username='', password='', remotefile='', localfile='', get=True):

    ssh_client = client.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    ssh_client.connect(remote_host,
                       port=22,
                       username=username,
                       password=password,
                       allow_agent=False,
                       look_for_keys=False)
    
    ftp_client = ssh_client.open_sftp()
    # TODO, fix this using argparse mutually exclusive arguments (get, put)
    if get:
        ftp_client.get(remotefile, localfile)
    else:
        ftp_client.put(remotefile, localfile)
    ftp_client.close()


def plot(hostname):
    ## TODO
    ## Make sure data is plotted correctly
    ##
    cpu_data = pd.read_csv(os.path.join(os.getcwd(), 'cpu.txt'),
                           skiprows=[0], delim_whitespace=True, skipfooter=3,
                           engine='python')
    # We don't want to plot individual cores (yet), too much clutter
    # We will just keep the averages    
    cpu_data = cpu_data[cpu_data['CPU'] == 'all']
    disk_data = pd.read_csv(os.path.join(os.getcwd(), 'disk.txt'),
                            skiprows=[0], delim_whitespace=True, skipfooter=1)
    mem_data = pd.read_csv(os.path.join(os.getcwd(), 'mem.txt'),
                            skiprows=[0], delim_whitespace=True, skipfooter=1)
    # Get unix time stamps                        
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

    # Convert data from string to float if necessary
    cpu_data = cpu_data.apply(pd.to_numeric, errors='ignore')
    disk_data = disk_data.apply(pd.to_numeric, errors='ignore')
    mem_data = mem_data.apply(pd.to_numeric, errors='ignore')
    
    # Please triple check that the legends match up to the coresponding lines
    ## TODO Better variable names here (line0, line1, etc)
    ## Or at least notes about what is going on possibly.
    # Plot cpu
    plt.figure(1)
    plt.subplots_adjust(bottom=0.2)
    plt.xticks(rotation=25)
    ax=plt.gca()
    ax.xaxis_date()
    xfmt = md.DateFormatter('%H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    plt.title(f'CPU usage on {remote_host}')
    lines = plt.plot(dates, cpu_data[cpu_data.columns[2:]])
    ax.legend(lines, [str(col) for col in list(cpu_data.columns[2:])])
    
    # Plot Disk I/O
    fig, axes = plt.subplots(2, sharex=True)
    fig.suptitle(f'Disk I/O on {remote_host}')
    lines0 = axes[0].plot(dates, disk_data[disk_data.columns[1:4]])
    axes[0].legend(lines0, disk_data[disk_data.columns[1:4]])
    lines1 = axes[1].plot(dates, disk_data[disk_data.columns[4:]])
    axes[1].legend(lines1, disk_data[disk_data.columns[4:]])
    plt.subplots_adjust(bottom=0.2)
    plt.xticks(rotation=25)
    ax=plt.gca()
    ax.xaxis_date()
    xfmt = md.DateFormatter('%H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    
    # Plot Memory
    fig, axes = plt.subplots(2, sharex=True)
    fig.suptitle(f'Memory usage on {remote_host}')
    lines0 = axes[0].plot(dates, mem_data[mem_data.columns[1:3]])
    axes[0].legend(lines0, mem_data[mem_data.columns[1:3]])
    lines1 = axes[1].plot(dates, mem_data[mem_data.columns[4:8]])
    axes[1].legend(lines1, mem_data[mem_data.columns[4:8]])
    plt.subplots_adjust(bottom=0.2)
    plt.xticks(rotation=25)
    ax=plt.gca()
    ax.xaxis_date()
    xfmt = md.DateFormatter('%H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    plt.show()
        
if __name__ == '__main__':
    # TODO, try catch for incorrect hostnames/passwords
    remote_host = input("Hostname or IP: ")
    username = input("username for SSH: ")
    password = getpass.getpass()
        
    # Generate Sar Data on remote host
    ssh(remote_host, username, password, 'sar -P ALL > /tmp/.sar_cpu.txt')
    ssh(remote_host, username, password, 'sar -b > /tmp/.sar_disk.txt')
    ssh(remote_host, username, password, 'sar -r > /tmp/.sar_mem.txt')
    # Pull sar data to local client
    scp(remote_host, username, password, '/tmp/.sar_cpu.txt', os.path.join(os.getcwd(), 'cpu.txt'))
    scp(remote_host, username, password, '/tmp/.sar_disk.txt', os.path.join(os.getcwd(), 'disk.txt'))
    scp(remote_host, username, password, '/tmp/.sar_mem.txt', os.path.join(os.getcwd(), 'mem.txt'))
    # Clean up after ourselves on remote host
    ssh(remote_host, username, password, 'rm -f /tmp/.sar_cpu.txt')
    ssh(remote_host, username, password, 'rm -f /tmp/.sar_disk.txt')
    ssh(remote_host, username, password, 'rm -f /tmp/.sar_mem.txt')

    plot(remote_host)

    
    ## TODO
    ## Don't use paramiko auto add policy, try catch instead.