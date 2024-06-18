# Copyright 2022 Onestein (<https://www.onestein.nl>)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).

import logging
from os.path import dirname, join

from vcr import VCR

from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase
from odoo.tools import mute_logger

logging.getLogger("vcr").setLevel(logging.WARNING)

recorder = VCR(
    record_mode="once",
    cassette_library_dir=join(dirname(__file__), "vcr_cassettes"),
    path_transformer=VCR.ensure_suffix(".yaml"),
    filter_headers=["Authorization"],
    decode_compressed_response=True,
)


class TestDeliverySendCloud(TransactionCase):
    @mute_logger("py.warnings")
    def setUp(self):
        super().setUp()
        integrations = (
            self.env["sendcloud.integration"].with_context(active_test=False).search([])
        )
        integrations.unlink()
        form = Form(self.env["sendcloud.integration.wizard"])
        wizard = form.save()
        wizard.base_url = "https://f482-185-247-144-87.eu.ngrok.io"
        with recorder.use_cassette("get_integration"):
            wizard.button_update()
        self.integration = self.env["sendcloud.integration"].search([])
        self.assertEqual(len(self.integration), 1)
        self.integration.public_key = "test"
        self.integration.secret_key = "test"
        self.integration.sendcloud_code = 241526

    @mute_logger("py.warnings")
    def test_01_sender_address(self):
        self.env["sendcloud.sender.address"].search([]).unlink()
        self.assertFalse(self.env["sendcloud.sender.address"].search([]))

        with recorder.use_cassette("sender_address"):
            self.env["sendcloud.sender.address"].sendcloud_sync_sender_address()

        self.assertEqual(len(self.env["sendcloud.sender.address"].search([])), 2)

    @mute_logger("py.warnings")
    def test_02_hs_code(self):
        """Retrieve Sendcloud shipping methods.
        Harmonized System Code is mandatory when shipping outside of EU
        """

        # Not any Sendcloud shipping method
        self.env["delivery.carrier"].search(
            [("delivery_type", "=", "sendcloud")]
        ).unlink()
        shipping_methods = self.env["delivery.carrier"].search(
            [("delivery_type", "=", "sendcloud")], limit=1
        )
        self.assertFalse(shipping_methods)

        # Retrieve Sendcloud shipping methods
        with recorder.use_cassette("shipping_methods"):
            self.env["delivery.carrier"].sendcloud_sync_shipping_method()
        shipping_method0 = self.env["delivery.carrier"].search(
            [("delivery_type", "=", "sendcloud")], limit=1
        )
        self.assertTrue(shipping_method0)

        # Sale order to outside EU
        sale_order = self.env.ref("sale.sale_order_1").copy()
        europe_codes = self.env.ref("base.europe").country_ids.mapped("code")
        partner_country = sale_order.partner_id.country_id.code
        self.assertFalse(partner_country in europe_codes)

        # Feature "Auto create invoice" not enabled by default
        self.assertFalse(sale_order.company_id.sendcloud_auto_create_invoice)

        # Set Sendcloud delivery method
        choose_delivery_form = Form(
            self.env["choose.delivery.carrier"].with_context(
                {
                    "default_order_id": sale_order.id,
                    "default_carrier_id": shipping_method0.id,
                }
            )
        )
        choose_delivery_wizard = choose_delivery_form.save()
        choose_delivery_wizard.button_confirm()

        # HS code consistency
        with self.assertRaisesRegex(
            ValidationError,
            "Harmonized System Code is mandatory when shipping outside of EU",
        ):
            sale_order.with_context(
                force_sendcloud_shipment_code="c9b2058d-2621-4ce5-afb0-f14e8e5565b6"
            ).action_confirm()

        # Set HS code and confirm order
        sale_order.mapped("order_line.product_id").write({"hs_code": "123"})
        with recorder.use_cassette("shipping_02"):
            sale_order.with_context(
                force_sendcloud_shipment_code="c9b2058d-2621-4ce5-afb0-f14e8e5565b6"
            ).action_confirm()

        # Not any invoice is created
        self.assertEqual(len(sale_order.invoice_ids), 0)

    def test_03_retrieve_integrations(self):
        with recorder.use_cassette("integrations"):
            self.integration.action_sendcloud_update_integrations()

    def test_04_auto_create_invoice(self):
        # Sale order to outside EU and "Auto create invoice" enabled
        sale_order = self.env.ref("sale.sale_order_1").copy()
        self.assertEqual(sale_order.partner_id.country_id.code, "US")
        sale_order.company_id.sendcloud_auto_create_invoice = True

        # No pre-existing invoices
        out_invoices = sale_order.invoice_ids.filtered(
            lambda i: i.move_type == "out_invoice"
        )
        self.assertFalse(out_invoices)

        out_invoices = sale_order._sendcloud_order_invoice()

        # Invoices created
        self.assertEqual(len(out_invoices), 1)
        self.assertEqual(out_invoices.move_type, "out_invoice")
        self.assertEqual(out_invoices.state, "posted")

    def test_05_retrieve_brands(self):
        with recorder.use_cassette("brands"):
            self.env["sendcloud.brand"].sendcloud_sync_brands()

    def test_06_retrieve_returns(self):
        with recorder.use_cassette("returns"):
            self.env["sendcloud.return"].sendcloud_sync_returns()

    def test_07_retrieve_statuses(self):
        with recorder.use_cassette("statuses"):
            self.env["sendcloud.parcel.status"].sendcloud_sync_parcel_statuses()

    def test_08_retrieve_parcels(self):
        with recorder.use_cassette("parcels"):
            self.env["sendcloud.parcel.status"].sendcloud_sync_parcel_statuses()
            self.env["sendcloud.parcel"].sendcloud_sync_parcels()

    def test_09_retrieve_invoices(self):
        with recorder.use_cassette("invoices"):
            self.env["sendcloud.invoice"].sendcloud_sync_invoices()

    def test_10_warehouse_address_wizard(self):
        """No error is raised"""
        form = Form(self.env["sendcloud.warehouse.address.wizard"])
        wizard = form.save()
        wizard.button_update()

    @mute_logger("py.warnings")
    def test_11_auto_create_invoice(self):
        """Test the "Auto create invoice" feature: when shipping outside EU"""
        # Sale order to outside EU
        sale_order = self.env.ref("sale.sale_order_1").copy()
        self.assertEqual(sale_order.partner_id.country_id.code, "US")
        sale_order.mapped("order_line.product_id").write({"hs_code": "123"})

        # Enable "Auto create invoice"
        sale_order.company_id.sendcloud_auto_create_invoice = True

        # retrieve Sendcloud shipping methods
        with recorder.use_cassette("shipping_methods"):
            self.env["delivery.carrier"].sendcloud_sync_shipping_method()
        shipping_method0 = self.env["delivery.carrier"].search(
            [("delivery_type", "=", "sendcloud")], limit=1
        )
        self.assertTrue(shipping_method0)

        # Set Sendcloud delivery method
        choose_delivery_form = Form(
            self.env["choose.delivery.carrier"].with_context(
                {
                    "default_order_id": sale_order.id,
                    "default_carrier_id": shipping_method0.id,
                }
            )
        )
        choose_delivery_wizard = choose_delivery_form.save()
        choose_delivery_wizard.button_confirm()

        # No pre-existing invoices
        out_invoices = sale_order.invoice_ids.filtered(
            lambda i: i.move_type == "out_invoice"
        )
        self.assertFalse(out_invoices)

        # Confirm order
        with recorder.use_cassette("shipping_01"):
            sale_order.with_context(
                force_sendcloud_shipment_code="bfdebf74-853d-4c32-9484-e0201426f888"
            ).action_confirm()

        # Invoice automatically created
        self.assertEqual(len(sale_order.invoice_ids), 1)
        self.assertEqual(sale_order.invoice_ids.move_type, "out_invoice")
        self.assertEqual(sale_order.invoice_ids.state, "posted")
