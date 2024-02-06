odoo.define('website_membership_registration.website_membership_registration', function (require) {
'use strict';

var publicWidget = require('web.public.widget');

publicWidget.registry.WebsiteMembershipRegistration = publicWidget.Widget.extend({
    selector: '.oe_website_membership_registration',
    events: {
        "change select[name=member_country_id]": "_onChangeAddressCountry",
        "change select[name=membership_product_id]": "_onChangeProduct",
    },

    /**
     * @override
     */
    start() {
        const res = this._super(...arguments);
        this._changeProduct();
        this._changeAddressCountry();
        return res
    },

    /**
     * @private
     * @param {Event} ev
     */
    // eslint-disable-next-line no-unused-vars
    _onChangeProduct: function (ev) {
        this._changeProduct();
    },

    /**
     * @private
     * @param {Event} ev
     */
    // eslint-disable-next-line no-unused-vars
    _onChangeAddressCountry: function (ev) {
        this._changeAddressCountry();
    },

    /**
     * @private
     * @param {Event} ev
     */
    // eslint-disable-next-line no-unused-vars
    _changeProduct: function (ev) {
        var product_el = $("#product_id")[0];
        var divAddress = $("div[id='address_data']");
        var inputStreet = $("input[name='member_street']");
        var inputStreet2 = $("input[name='member_street2']");
        var inputCity = $("input[name='member_city']");
        var inputZip = $("input[name='member_zip']");
        var selectCountries = $("select[name='member_country_id']");
        var selectStates = $("select[name='member_state_id']");
        if (!product_el.selectedOptions[0] || !product_el.selectedOptions[0].getAttribute("data-is_paid")) {
            // Empty all address fields, make address fields non required, then hide the whole address block
            inputStreet.val('')
            inputStreet2.val('')
            inputCity.val('')
            inputZip.val('')
            selectCountries.data('init', 0);
            selectCountries.val('')
            selectStates.data('init', 0);
            selectStates.val('')
            this._changeAddressCountry();
            divAddress.hide();
            inputStreet.get(0).toggleAttribute('required', false);
            inputCity.get(0).toggleAttribute('required', false);
            inputZip.get(0).toggleAttribute('required', false);
            selectCountries.get(0).toggleAttribute('required', false);
            return;
        }

            // Display address block + make street, city and country required, then invoke onchange country
            divAddress.show();
            inputStreet.get(0).toggleAttribute('required', true);
            inputCity.get(0).toggleAttribute('required', true);
            inputZip.get(0).toggleAttribute('required', true);
            selectCountries.get(0).toggleAttribute('required', true);
            this._changeAddressCountry();

    },

    /**
     * @private
     */
    _changeAddressCountry: function () {
        if (!$("#country_id").val()) {
            // If country is empty, also empty state and set zip and state non mandatory
            var selectStates = $("select[name='member_state_id']");
            selectStates.val('').parent('div').hide();
            selectStates.data('init', 0);
            selectStates.html('');
            if ($("input[name='member_zip']").length) {
                $("input[name='member_zip']").get(0).toggleAttribute('required', false);
                if ($("label[for='member_zip'] > span.s_website_form_mark").length) {
                    $("label[for='member_zip'] > span.s_website_form_mark").attr('style', 'display: none');
                }
            }
            if ($("input[name='member_state_id']").length) {
                $("select[name='member_state_id']").get(0).toggleAttribute('required', false);
                if ($("label[for='member_state_id'] > span.s_website_form_mark").length) {
                    $("label[for='member_state_id'] > span.s_website_form_mark").attr('style', 'display: none');
                }
            }
            return;
        }
        this._rpc({
            route: "/shop/country_infos/" + $("#country_id").val(),
            params: {
                mode: 'billing',
            },
        }).then(function (data) {
            // Populate states and display
            var $selectStates = $("select[name='member_state_id']");
            $("#select[name='member_state_id'] option:not(:first)"). remove();
            // Dont reload state at first loading (done in qweb)
            if ($selectStates.data('init')===0 || $selectStates.find('option').length===1) {
                if (data.states.length || data.state_required) {
                    _.each(data.states, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0])
                            .attr('data-code', x[2]);
                        $selectStates.append(opt);
                    });

                    $selectStates.parent('div').show();
                } else {
                    $selectStates.val('').parent('div').hide();
                }
                $selectStates.data('init', 0);
            } else {
                $selectStates.data('init', 0);
            }

            var zip_style = 'display: none';
            if (data.zip_required) {
                zip_style = '';
            }
            var state_style = 'display: none';
            if (data.state_required) {
                state_style = '';
            }
            if ($("input[name='member_zip']").length) {
                $("input[name='member_zip']").get(0).toggleAttribute('required', Boolean(data.zip_required));
                if ($("label[for='member_zip'] > span.s_website_form_mark").length) {
                    $("label[for='member_zip'] > span.s_website_form_mark").attr('style', zip_style);
                }
            }
            if ($("select[name='member_state_id']").length) {
                $("select[name='member_state_id']").get(0).toggleAttribute('required', Boolean(data.state_required));
                if ($("label[for='member_state_id'] > span.s_website_form_mark").length) {
                    $("label[for='member_state_id'] > span.s_website_form_mark").attr('style', state_style);
                }
            }
        });
    },

});

return {
    WebsiteMembershipRegistration: publicWidget.registry.WebsiteMembershipRegistration,
};

});
