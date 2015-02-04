# Copyright 2014 IBM Corp.
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from neutron.i18n import _LW
from neutron.openstack.common import log as logging

from pypowervm import adapter
from pypowervm.wrappers import client_network_adapter as cnawrap
from pypowervm.wrappers import logical_partition as lwrap
from pypowervm.wrappers import network as nwrap

LOG = logging.getLogger(__name__)


class NetworkBridgeUtils(object):
    '''
    This class provides a set of methods that can be used for calling in
    to the PowerVM REST API (via the python wrapper) and parsing the results
    in such a way that can be easily consumed by the agent.

    The goal of this class is to enable the agent to be focused on 'flow' and
    this holds the implementation for the methods.
    '''

    def __init__(self, pvm_server_ip, username, password, host_id):
        '''
        Initializes the utility class.

        :param pvm_server_ip: The IP address of the PowerVM API server.
        :param username: The user name for API operations.
        :param password: The password for the API operations.
        :param host_id: The API's host UUID for the server being managed.
        '''
        session = adapter.Session(pvm_server_ip, username, password,
                                  certpath=False)
        self.adapter = adapter.Adapter(session)
        self.host_id = host_id

    def norm_mac(self, mac):
        '''
        Will return a MAC Address that is normalized to match that of the
        pypowervm API.

        That means that the format will be without colons and upper cased.

        :param mac: A mac address.  Ex. 12:34:56:78:90:ab
        :returns: A mac that matches the format of the pypowervm api.
                  Ex. 1234567890AB
        '''
        return mac.upper().replace(":", "")

    def find_client_adpt_for_mac(self, mac, client_adpts=None):
        '''
        Will return the appropriate client adapter for a given mac address.

        :param mac: The mac address of the client adapter.
        :param client_adpts: The Client Adapters.  Should be passed in for
                             performance reasons.  If not, will invoke
                             list_client_adpts.
        :returns: The Client Adapter for the mac.  If one isn't found, then
                  None will be returned.
        '''
        if not client_adpts:
            client_adpts = self.list_client_adpts()

        mac = self.norm_mac(mac)

        for client_adpt in client_adpts:
            if client_adpt.mac == mac:
                return client_adpt

        # None was found.
        return None

    def list_client_adpts(self):
        '''
        Lists all of the Client Network Adapters for the running virtual
        machines.
        '''
        vms = self._list_vm_entries()
        total_cnas = []

        for vm in vms:
            for cna_uri in vm.cna_uris:
                cna_entry = self.adapter.readbyhref(cna_uri)
                cna = cnawrap.ClientNetworkAdapter(cna_entry)
                total_cnas.append(cna)

        return total_cnas

    def _list_vm_entries(self):
        '''
        Returns a List of all of the Client (non-VIOS) VMs on the system.
        Does not take into account whether or not it is managed by
        OpenStack.
        '''
        vm_feed = self.adapter.read('ManagedSystem', self.host_id,
                                    'LogicalPartition')
        vm_entries = vm_feed.feed.entries
        vms = []
        for vm_entry in vm_entries:
            vms.append(lwrap.LogicalPartition(vm_entry))
        return vms

    def list_bridges(self):
        '''
        Queries for the NetworkBridges on the system.  Will return the
        wrapper objects that describe Network Bridges.
        '''
        resp = self.adapter.read('ManagedSystem', self.host_id,
                                 'NetworkBridge')
        entries = resp.feed.entries
        net_bridges = []

        for entry in entries:
            net_bridges.append(nwrap.NetworkBridge(entry))

        if len(net_bridges) == 0:
            LOG.warn(_LW('No NetworkBridges detected on the host.'))

        return net_bridges

    def add_vlan(self, net_bridge, load_group, vlan_id):
        '''
        This method will add a VLAN to a given LoadGroup within the
        Network Bridge.

        It assumes that there are enough VLANs available on the
        Load Group to support the request.

        :param net_bridge: The NetworkBridge wrapper object.
        :param load_group: The LoadGroup wrapper object within the net_bridge
                           to add the VLAN to.
        :param vlan_id: The VLAN to add to the NetworkBridge.
        '''
        # TODO(thorst) implement
        pass

    def remove_vlan(self, net_bridge, load_group, vlan_id):
        '''
        This method will remove a VLAN from a given NetworkBridge.  If the
        VLAN is the last VLAN on the specific LoadGroup, it will delete the
        LoadGroup from the system (unless it is the 'primary' Load Group
        on the Network Bridge).

        :param net_bridge: The NetworkBridge wrapper object that contains the
                           LoadGroup.
        :param load_groupd: The LoadGroup wrapper object that will have the
                            VLAN removed from it.
        :param vlan_id: The VLAN to remove from the NetworkBridge.
        '''
        # TODO(thorst) impelement
        pass

    def is_vlan_on_bridge(self, net_bridge, vlan_id):
        '''
        Will determin if the VLAN is 'on the NetworkBridge'.  This means
        one of the following conditions is met.
         - Is an addl_vlan on any LoadGroup within the NetworkBridge.
         - Is the primary VLAN of the primary LoadGroup.  Primary LoadGroup
           means the first LoadGroup on the Network Bridge.

        This method will return false if one of the following occurs:
         - Is a primary VLAN of a NON-primary LoadGroup.
         - Is not on any of the LoadGroups.

        :param net_bridge: The NetworkBridge to query through all VLANs.
        :param vlan_id: The VLAN ID to query for.
        :return: True if the VLAN is on the NetworkBridge (see conditions
                 above). Otherwise returns False.
        '''
        # TODO(thorst) impelement
        pass

    def _is_vlan_non_primary_pvid(self, net_bridge, vlan_id):
        '''
        Returns whether or not the VLAN is on a non-primary LoadGroup as a
        Primary VLAN ID.

        :param net_bridge: The NetworkBridge wrapper object that contains all
                           of the Load Groups.
        :param vlan_id: The VLAN to query against the NetworkBridge.
        :return: True if VLAN is a primary VLAN ID on a non-primary VEA.
        '''
        # TODO(thorst) implement
        return False

    def _find_valid_toss_vid(self, net_bridge, all_net_bridges=None):
        '''
        This method will find a VLAN ID that can be used for a non-primary
        LoadGroup on a given NetworkBridge.  This is a VLAN that is not used
        by any workload that can be used as a placeholder.

        No traffic will be routed through this VLAN.

        :param net_bridge: The NetworkBridge wrapper object that will make
                           use of the place holder VLAN.
        :param all_net_bridges: A listing of all of the NetworkBridge wrapper
                                objects on the system.
        :return: An integer value that is valid for use as a non-primary VEA
                 PVID.
        '''
        # TODO(thorst) implement
        pass
