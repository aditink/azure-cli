# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest


class AzureReservationsTests(ScenarioTest):

    def _validate_reservation_order(self, reservation_order):
        self.assertIsNotNone(reservation_order)
        self.assertTrue(reservation_order['etag'])
        self.assertTrue(reservation_order['id'])
        self.assertTrue(reservation_order['name'])
        self.assertTrue(reservation_order['originalQuantity'])
        self.assertTrue(reservation_order['provisioningState'])
        self.assertTrue(reservation_order['requestDateTime'])
        self.assertTrue(reservation_order['reservations'])
        self.assertTrue(reservation_order['term'])
        self.assertTrue(reservation_order['type'])
        self.assertTrue(reservation_order['type'] == 'Microsoft.Capacity/reservationOrders')

    def _validate_reservation(self, reservation):
        self.assertIsNotNone(reservation)
        self.assertTrue(reservation['location'])
        self.assertTrue(len(reservation['location']) > 0)
        self.assertTrue(reservation['etag'])
        self.assertTrue(reservation['etag'] > 0)
        self.assertTrue(reservation['id'])
        self.assertTrue(reservation['name'])
        self.assertTrue(reservation['sku'])
        self.assertTrue(reservation['properties'])
        self.assertTrue(reservation['type'])
        self.assertTrue(reservation['type'] == 'Microsoft.Capacity/reservationOrders/reservations')

    def test_get_applied_reservation_order_ids(self):
        self.kwargs.update({
            'subscription': 'a6cca743-ee25-481c-8626-e5362d7bf0b9'
        })
        result = self.cmd('reservations reservation-order-id list --subscription-id {subscription}') \
            .get_output_in_json()
        for order_id in result['reservationOrderIds']['value']:
            self.assertIn('/providers/Microsoft.Capacity/reservationorders/', order_id)

    def test_list_reservation_order(self):
        reservation_order_list = self.cmd('reservations reservation-order list').get_output_in_json()
        self.assertIsNotNone(reservation_order_list)
        for order in reservation_order_list:
            self._validate_reservation_order(order)
            self.assertIn('/providers/microsoft.capacity/reservationOrders/', order['id'])
            self.assertGreater(order['etag'], 0)
            for reservation in order['reservations']:
                self.assertTrue(reservation['id'])

    def test_get_reservation_order(self):
        self.kwargs.update({
            'reservation_order_id': '8f962b1d-b9f6-4b4a-9732-e1b3ceadc391'
        })
        command = 'reservations reservation-order show --reservation-order-id {reservation_order_id}'
        reservation_order = self.cmd(command).get_output_in_json()
        self._validate_reservation_order(reservation_order)
        self.assertIn('/providers/microsoft.capacity/reservationOrders/', reservation_order['id'])
        self.assertGreater(reservation_order['etag'], 0)

    def test_list_reservation(self):
        self.kwargs.update({
            'reservation_order_id': '8f962b1d-b9f6-4b4a-9732-e1b3ceadc391'
        })
        reservation_list = self.cmd('reservations reservation list --reservation-order-id {reservation_order_id}') \
            .get_output_in_json()
        self.assertIsNotNone(reservation_list)
        for reservation in reservation_list:
            self.assertIn(self.kwargs['reservation_order_id'], reservation['name'])
            self.assertGreater(reservation['etag'], 0)
            self.assertEqual('Microsoft.Capacity/reservationOrders/reservations', reservation['type'])

    def test_get_reservation(self):
        self.kwargs.update({
            'reservation_order_id': '8f962b1d-b9f6-4b4a-9732-e1b3ceadc391',
            'reservation_id': '343cdc00-d1bf-45aa-8512-2c576601c49a'
        })
        reservation = self.cmd('reservations reservation show  --reservation-order-id {reservation_order_id} '
                               '--reservation-id {reservation_id}').get_output_in_json()
        self.assertIn(self.kwargs['reservation_order_id'], reservation['name'])
        self.assertGreater(reservation['etag'], 0)
        self.assertGreater(reservation['properties']['quantity'], 0)
        self.assertEqual('Microsoft.Capacity/reservationOrders/reservations', reservation['type'])

    def test_list_reservation_history(self):
        self.kwargs.update({
            'reservation_order_id': '8f962b1d-b9f6-4b4a-9732-e1b3ceadc391',
            'reservation_id': '343cdc00-d1bf-45aa-8512-2c576601c49a'
        })
        history = self.cmd('reservations reservation list-history --reservation-order-id {reservation_order_id}'
                           ' --reservation-id {reservation_id}').get_output_in_json()
        self.assertGreater(len(history), 0)
        for entry in history:
            self.assertGreater(entry['etag'], 0)
            name_format = '{}/{}'.format(self.kwargs['reservation_order_id'], self.kwargs['reservation_id'])
            self.assertIn(name_format, entry['name'])

    def test_get_catalog(self):
        self.kwargs.update({
            'subscription': 'a6cca743-ee25-481c-8626-e5362d7bf0b9',
            'type': 'AppService',
            'location': 'westus2'
        })
        # TODO throw CLI Error.
        catalog = self.cmd(
            'reservations catalog show --subscription-id {subscription} --reserved-resource-type {type} --location {location}').get_output_in_json()
        self.assertGreater(len(catalog), 0)
        for entry in catalog:
            self.assertGreater(len(entry['terms']), 0)
            self.assertGreater(len(entry['skuProperties']), 0)
            self.assertIsNotNone(entry['resourceType'])
            self.assertIsNotNone(entry['name'])

    def test_update_reservation(self):
        self.kwargs.update({
            'reservation_order_id': '8f962b1d-b9f6-4b4a-9732-e1b3ceadc391',
            'reservation_id': '343cdc00-d1bf-45aa-8512-2c576601c49a',
            'scope': '/subscriptions/a6cca743-ee25-481c-8626-e5362d7bf0b9',
            'instance_flexibility': 'On'
        })

        single_reservation = self.cmd('reservations reservation update --reservation-order-id {reservation_order_id}'
                                      ' --reservation-id {reservation_id} -t Single -s {scope}'
                                      ' --instance-flexibility {instance_flexibility}').get_output_in_json()
        self.assertEqual('Single', single_reservation['properties']['appliedScopeType'])

        shared_reservation = self.cmd('reservations reservation update --reservation-order-id {reservation_order_id} '
                                      '--reservation-id {reservation_id} -t Shared'
                                      ' --instance-flexibility {instance_flexibility}').get_output_in_json()
        self.assertEqual('Shared', shared_reservation['properties']['appliedScopeType'])

    def test_split_and_merge(self):
        self.kwargs.update({
            'reservation_order_id': '1209c113-0201-43fc-93d5-9ed1eeecefbe',
            'reservation_id': 'dc7e4968-79b8-445e-8f83-9a1268a8aba1',
            'quantity1': 1,
            'quantity2': 3
        })

        original_reservation = self.cmd('reservations reservation show  --reservation-order-id {reservation_order_id}'
                                        ' --reservation-id {reservation_id}').get_output_in_json()
        original_quantity = original_reservation['properties']['quantity']

        split_items = self.cmd('reservations reservation split --reservation-order-id {reservation_order_id} '
                               '--reservation-id {reservation_id} -1 {quantity1} -2 {quantity2}').get_output_in_json()
        self.assertIsNotNone(split_items)

        quantity_sum = 0
        split_ids = []
        for item in split_items:
            self._validate_reservation(item)
            if 'Succeeded' in item['properties']['provisioningState']:
                item_id = item['name'].split('/')[1]
                split_ids.append(item_id)
                quantity_sum += item['properties']['quantity']
        self.assertEqual(original_quantity, quantity_sum)
        self.assertEqual(2, len(split_ids))

        self.kwargs.update({
            'split_id1': split_ids[0],
            'split_id2': split_ids[1]
        })
        merge_items = self.cmd('reservations reservation merge --reservation-order-id {reservation_order_id} -1 '
                               '{split_id1} -2 {split_id2}').get_output_in_json()
        self.assertIsNotNone(merge_items)
        for item in merge_items:
            self._validate_reservation(item)
            if 'Succeeded' in item['properties']['provisioningState']:
                self.assertEqual(quantity_sum, item['properties']['quantity'])

    def test_calculate_reservation_order(self):
        self.kwargs.update({
            'subid': 'a6cca743-ee25-481c-8626-e5362d7bf0b9',
            'sku': 'standard_b1ls',
            'location': 'westus',
            'reservedResourceType': 'VirtualMachines',
            'term': 'P1Y',
            'quantity': '2',
            'displayName': 'test',
            'appliedScopes': 'Shared',
            'instanceFlexibility': 'Off',
            'billingPlan': 'Monthly',
            'appliedScopeType': 'Shared'
        })
        response = self.cmd('reservations reservation-order calculate --sku {sku} --location {location} --reserved-resource-type {reservedResourceType}'
                            ' --billing-scope {subid} --term {term} --billing-plan {billingPlan} --display-name {displayName}'
                            ' --quantity {quantity} --applied-scope-type {appliedScopeType}').get_output_in_json()
        self.assertIsNotNone(response)
        self.assertIsNotNone(response['properties']['reservationOrderId'])
        self.assertEqual('standard_b1ls', response['properties']['skuDescription'])

    def test_purchase_reservation_order(self):
        self.kwargs.update({
            'roid': 'f7a08850-666d-4d2a-b531-c5ce9ece2212',
            'subid': 'a6cca743-ee25-481c-8626-e5362d7bf0b9',
            'sku': 'standard_b1ls',
            'location': 'westeurope',
            'reservedResourceType': 'VirtualMachines',
            'term': 'P3Y',
            'quantity': '1',
            'displayName': '877194f4-a43d-4e92-9782-69fd59faa8d8',
            'appliedScopes': 'Shared',
            'instanceFlexibility': 'On',
            'billingPlan': 'Monthly',
            'appliedScopeType': 'Shared'
        })
        response = self.cmd('reservations reservation-order purchase --reservation-order-id {roid} --sku {sku} --location {location} --reserved-resource-type {reservedResourceType}'
                            ' --billing-scope {subid} --term {term} --billing-plan {billingPlan} --display-name {displayName}'
                            ' --quantity {quantity} --applied-scope-type {appliedScopeType}').get_output_in_json()
        self.assertIsNotNone(response)
        self.assertGreater(response['etag'], 0)
        self.assertIsNotNone(response['term'])
        self.assertIsNotNone(response['billingPlan'])
        self.assertIsNotNone(response['displayName'])
        self.assertEqual(2, response['originalQuantity'])
