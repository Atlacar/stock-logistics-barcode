# © 2012-2014 Guewen Baconnier (Camptocamp SA)
# © 2015 Roberto Lizana (Trey)
# © 2016 Pedro M. Baeza
# © 2018 Xavier Jimenez (QubiQ)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    barcode_ids = fields.One2many(
        comodel_name="product.barcode",
        inverse_name="product_id",
        string="Barcodes",
        auto_join=True,
    )
    barcode = fields.Char(
        string="Main barcode",
        compute="_compute_barcode",
        store=True,
        inverse="_inverse_barcode",
        compute_sudo=True,
    )

    @api.depends("barcode_ids.name", "barcode_ids.sequence")
    def _compute_barcode(self):
        for product in self:
            product.barcode = product.barcode_ids[:1].name

    def _inverse_barcode(self):
        """Store the product's barcode value in the barcode model."""
        barcodes_to_unlink = self.env["product.barcode"]
        create_barcode_vals_list = []
        for product in self:
            if not product.barcode:
                barcodes_to_unlink |= product.barcode_ids
            elif product.barcode_ids:
                product.barcode_ids[0].name = product.barcode
            else:
                create_barcode_vals_list.append(product._prepare_barcode_vals())
        if barcodes_to_unlink:
            barcodes_to_unlink.unlink()
        if create_barcode_vals_list:
            self.env["product.barcode"].create(create_barcode_vals_list)

    def _prepare_barcode_vals(self):
        self.ensure_one()
        return {
            "product_id": self.id,
            "name": self.barcode,
        }

    @api.model
    def _search(self, domain, *args, **kwargs):
        domain = self._get_barcode_search_domain_multi(domain)
        return super()._search(domain, *args, **kwargs)

    @api.model
    def _get_barcode_search_domain_multi(self, domain):
        """Search every barcode of the product instead of the main one only.

        Leaves on an empty value (``barcode = False`` / ``barcode != False``)
        keep targeting the stored main barcode: it is empty if and only if the
        product has no barcode at all.
        """
        new_domain = []
        for item in domain or []:
            if (
                isinstance(item, (list, tuple))
                and len(item) == 3
                and item[0] == "barcode"
                and item[2]
            ):
                item = ("barcode_ids.name", item[1], item[2])
            new_domain.append(item)
        return new_domain
