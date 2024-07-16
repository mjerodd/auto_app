from panos import network
from panos import firewall
from panos import policies
from panos import ha
import os
from django.conf import settings


class ChurchFirewall:

    zones = ['zone_to-pa-hub', 'zone-to-hub', 'zone-to-branch', 'zone-internet', 'zone-internal', 'noc_transit_router',
             'noc_infrastructure_mgmt',
             'corp_wireless_mgmt', 'corp_casino_operations', 'corp_client_audiovisual', 'corp_client_general',
             'corp_client_pos', 'corp_client_utility',
             'corp_client_voip', 'corp_facility_general', 'corp_printer_general', 'internet_public', 'internet_open',
             'corp_server_casino', 'corp_server_general', 'corp_server_voip', 'corp_tracd nsit_router'
             ]

    def __init__(self, firewall_ip):
        self.api_user =  settings.API_USER
        self.api_password = settings.API_PASSWORD
        self.fw_conn = firewall.Firewall(hostname=firewall_ip, api_username=self.api_user, api_password=self.api_password)

    def initial_clean(self):
        vwire = network.VirtualWire(name="default-vwire")
        self.fw_conn.add(vwire)
        vwire.delete()

        ruleb = policies.Rulebase()
        self.fw_conn.add(ruleb)
        del_rule = policies.SecurityRule(name="rule1")
        ruleb.add(del_rule)
        del_rule.delete()

        trust = network.Zone(name="trust")
        untrust = network.Zone(name="untrust")
        self.fw_conn.add(trust)
        self.fw_conn.add(untrust)
        trust.delete()
        untrust.delete()

        int_1 = network.EthernetInterface(name="ethernet1/4")
        int_2 = network.EthernetInterface(name="ethernet1/5")
        self.fw_conn.add(int_1)
        self.fw_conn.add(int_2)
        int_1.delete()
        int_2.delete()

        vr = network.VirtualRouter(name="default_lab")
        self.fw_conn.add(vr)
        vr.delete()

    def ha_setup(self):
        ha_conf = ha.HighAvailability(enabled=True, group_id=10, state_sync=True, passive_link_state='auto',
                                      peer_ip='10.1.1.2', peer_ip_backup='10.1.1.6')
        ha_eth1 = network.EthernetInterface("ethernet1/7", mode="ha")
        ha_eth2 = network.EthernetInterface("ethernet1/8", mode="ha")
        self.fw_conn.add(ha_eth1)
        self.fw_conn.add(ha_eth2)
        ha_eth1.create()
        ha_eth2.create()
        self.fw_conn.commit()

        ha1_int = ha.HA1("10.1.1.1", "255.255.255.0", port="ethernet1/7")
        ha2_int = ha.HA2("10.2.2.2", "255.255.255.0", port="ethernet1/8")
        self.fw_conn.add(ha_conf)
        ha_conf.add(ha1_int)
        ha_conf.add(ha2_int)
        ha_conf.create()
        self.fw_conn.commit()

    def disable_ztp(self):
        command = "set system ztp disable"
        self.fw_conn.op(cmd=command, xml=True)

    def create_zone(self, zone):
        add_zone = network.Zone(name=zone, mode="layer3")
        self.fw_conn.add(add_zone)
        add_zone.create()

    def init_net(self):
        vr = network.VirtualRouter(name='sdwan')
        self.fw_conn.add(vr)
        vr.create()

        agg_int = network.AggregateInterface(name='ae1', mode='layer3', lacp_enable=True, lacp_mode='active',
                                             lacp_rate='slow')
        self.fw_conn.add(agg_int)
        agg_int.create()

        for zone in self.zones:
            self.create_zone(zone)
        self.fw_conn.commit()

        phys_int = network.EthernetInterface(name='ethernet1/5', mode='aggregate-group', aggregate_group='ae1')
        self.fw_conn.add(phys_int)
        phys_int.create()

        wan_sub_int = network.Layer3Subinterface('ethernet1/1.1851', tag=1851, ip=('4.4.4.4',))
        self.fw_conn.add(wan_sub_int)
        wan_sub_int.set_zone('internet_public', update=True, running_config=True)
        wan_sub_int.set_virtual_router('sdwan', update=True, running_config=True)

        wan_sub_int.create()
        self.fw_conn.commit()




