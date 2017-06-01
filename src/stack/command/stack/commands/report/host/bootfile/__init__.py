# @SI_Copyright@
# @SI_Copyright@


import os
import stack.commands
from stack.exception import *

class Command(stack.commands.Command,
	stack.commands.HostArgumentProcessor):
	"""
	Output the PXE file for a host
	<arg name="host" type="string" repeat="1">
	One or more hostnames
	</arg>
	<param name="action" type="string" optional="0">
	Generate PXE file for a specified action
	</param>
	"""


	def run(self, params, args):

		hosts = self.getHostnames(args, managed_only=True)

		(action,) = self.fillParams([
			('action', None)
                ])

                ha = {}
                for host in hosts:
                        ha[host] = { 
                                'host'       : host,
                                'action'     : None,
                                'type'       : action,
                                'attrs'      : {}
                        }

                for row in self.call('list.host.attr', hosts):
                        ha[row['host']]['attrs'][row['attr']] = row['value']
                        
                if not action: # param can override the db
                        for row in self.call('list.host.boot', hosts):
                                ha[row['host']]['type'] = row['action']

                for row in self.call('list.host', hosts):
                        h = ha[row['host']]
                        if h['type'] == 'install':
                               h['action'] = row['installaction']
                        elif h['type'] == 'os':
                               h['action'] = row['osaction']
                        h['os']        = row['os']
                        h['appliance'] = row['appliance']

                ba = {}
                for row in self.call('list.bootaction'):
                        ba[(row['bootaction'], row['type'], row['os'])] = row

                for host in hosts:
                        h   = ha[host]
                        key = (h['action'], h['type'], None)
                        if ba.has_key(key):
                                b = ba[key]
                                h['kernel']  = b['kernel']
                                h['ramdisk'] = b['ramdisk']
                                h['args']    = b['args']
                        key = (h['action'], h['type'], h['os'])
                        if ba.has_key(key):
                                b = ba[key]
                                h['kernel']  = b['kernel']
                                h['ramdisk'] = b['ramdisk']
                                h['args']    = b['args']

                argv = []
                for host in hosts:
                        argv.append(host)
                argv.append('expanded=true')
		for row in self.call('list.host.interface', argv):
                        h   = ha[row['host']]
			ip  = row['ip']
			pxe = row['pxe']

                        if h['appliance'] == 'frontend':
                                h['filename'] = None
                        elif ip and pxe:
				#
				# Compute the HEX IP filename for the host
				#
				hexstr = ''
				for i in string.split(ip, '.'):
					hexstr += '%02x' % (int(i))
                                h['filename'] = hexstr.upper()
                                h['ip']       = ip
                                h['mask']     = row['mask']
                                h['gateway']  = row['gateway']

		self.beginOutput()
		self.runPlugins(ha)
		self.endOutput(padChar='', trimOwner=True)

