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

import mock
from oslo_config import cfg

from neutron.api.rpc.callbacks import events
from neutron.api.rpc.callbacks import resources
from neutron.common import exceptions as n_exc
from neutron import context
from neutron import manager
from neutron.objects import base as base_object
from neutron.objects.qos import policy as policy_object
from neutron.objects.qos import rule as rule_object
from neutron.plugins.common import constants
from neutron.tests import base


DB_PLUGIN_KLASS = 'neutron.db.db_base_plugin_v2.NeutronDbPluginV2'


class TestQosPlugin(base.BaseTestCase):

    def setUp(self):
        super(TestQosPlugin, self).setUp()
        self.setup_coreplugin()

        mock.patch('neutron.db.api.create_object').start()
        mock.patch('neutron.db.api.update_object').start()
        mock.patch('neutron.db.api.delete_object').start()
        mock.patch('neutron.db.api.get_object').start()
        mock.patch(
            'neutron.objects.qos.policy.QosPolicy.obj_load_attr').start()
        self.registry_p = mock.patch(
            'neutron.api.rpc.callbacks.registry.notify')
        self.registry_m = self.registry_p.start()
        cfg.CONF.set_override("core_plugin", DB_PLUGIN_KLASS)
        cfg.CONF.set_override("service_plugins", ["qos"])

        mgr = manager.NeutronManager.get_instance()
        self.qos_plugin = mgr.get_service_plugins().get(
            constants.QOS)
        self.ctxt = context.Context('fake_user', 'fake_tenant')
        self.policy_data = {
            'policy': {'id': 7777777,
                       'tenant_id': 888888,
                       'name': 'test-policy',
                       'description': 'Test policy description',
                       'shared': True}}

        self.rule_data = {
            'bandwidth_limit_rule': {'id': 7777777,
                                     'max_kbps': 100,
                                     'max_burst_kbps': 150}}

        self.policy = policy_object.QosPolicy(
            context, **self.policy_data['policy'])

        self.rule = rule_object.QosBandwidthLimitRule(
            context, **self.rule_data['bandwidth_limit_rule'])

    def _validate_registry_params(self, event_type):
        self.registry_m.assert_called_once_with(
            resources.QOS_POLICY,
            event_type,
            mock.ANY)
        self.assertIsInstance(
            self.registry_m.call_args[0][2], policy_object.QosPolicy)

    def test_add_policy(self):
        self.qos_plugin.create_policy(self.ctxt, self.policy_data)
        self.assertFalse(self.registry_m.called)

    def test_update_policy(self):
        fields = base_object.get_updatable_fields(
            policy_object.QosPolicy, self.policy_data['policy'])
        self.qos_plugin.update_policy(
            self.ctxt, self.policy.id, {'policy': fields})
        self._validate_registry_params(events.UPDATED)

    @mock.patch('neutron.db.api.get_object', return_value=None)
    def test_delete_policy(self, *mocks):
        self.qos_plugin.delete_policy(self.ctxt, self.policy.id)
        self._validate_registry_params(events.DELETED)

    def test_create_policy_rule(self):
        with mock.patch('neutron.objects.qos.policy.QosPolicy.get_by_id',
                        return_value=self.policy):
            self.qos_plugin.create_policy_bandwidth_limit_rule(
                self.ctxt, self.policy.id, self.rule_data)
            self._validate_registry_params(events.UPDATED)

    def test_update_policy_rule(self):
        with mock.patch('neutron.objects.qos.policy.QosPolicy.get_by_id',
                        return_value=self.policy):
            self.qos_plugin.update_policy_bandwidth_limit_rule(
                self.ctxt, self.rule.id, self.policy.id, self.rule_data)
            self._validate_registry_params(events.UPDATED)

    def test_delete_policy_rule(self):
        with mock.patch('neutron.objects.qos.policy.QosPolicy.get_by_id',
                        return_value=self.policy):
            self.qos_plugin.delete_policy_bandwidth_limit_rule(
                self.ctxt, self.rule.id, self.policy.id)
            self._validate_registry_params(events.UPDATED)

    def test_get_policy_for_nonexistent_policy(self):
        with mock.patch('neutron.objects.qos.policy.QosPolicy.get_by_id',
                        return_value=None):
            self.assertRaises(
                n_exc.QosPolicyNotFound,
                self.qos_plugin.get_policy,
                self.ctxt, self.policy.id)

    def test_get_policy_bandwidth_limit_rule_for_nonexistent_policy(self):
        with mock.patch('neutron.objects.qos.policy.QosPolicy.get_by_id',
                        return_value=None):
            self.assertRaises(
                n_exc.QosPolicyNotFound,
                self.qos_plugin.get_policy_bandwidth_limit_rule,
                self.ctxt, self.rule.id, self.policy.id)

    def test_get_policy_bandwidth_limit_rules_for_nonexistent_policy(self):
        with mock.patch('neutron.objects.qos.policy.QosPolicy.get_by_id',
                        return_value=None):
            self.assertRaises(
                n_exc.QosPolicyNotFound,
                self.qos_plugin.get_policy_bandwidth_limit_rules,
                self.ctxt, self.policy.id)

    def test_create_policy_rule_for_nonexistent_policy(self):
        with mock.patch('neutron.objects.qos.policy.QosPolicy.get_by_id',
                        return_value=None):
            self.assertRaises(
                n_exc.QosPolicyNotFound,
                self.qos_plugin.create_policy_bandwidth_limit_rule,
                self.ctxt, self.policy.id, self.rule_data)

    def test_update_policy_rule_for_nonexistent_policy(self):
        with mock.patch('neutron.objects.qos.policy.QosPolicy.get_by_id',
                        return_value=None):
            self.assertRaises(
                n_exc.QosPolicyNotFound,
                self.qos_plugin.update_policy_bandwidth_limit_rule,
                self.ctxt, self.rule.id, self.policy.id, self.rule_data)

    def test_delete_policy_rule_for_nonexistent_policy(self):
        with mock.patch('neutron.objects.qos.policy.QosPolicy.get_by_id',
                        return_value=None):
            self.assertRaises(
                n_exc.QosPolicyNotFound,
                self.qos_plugin.delete_policy_bandwidth_limit_rule,
                self.ctxt, self.rule.id, self.policy.id)
