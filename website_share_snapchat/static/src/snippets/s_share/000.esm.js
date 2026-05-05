import publicWidget from '@web/legacy/js/public/public_widget';
publicWidget.registry.share.include({

        /**
         * @override
         */
        start() {
            this._super(...arguments);

            const urlRegex = /(\?(?:|.*&)(?:attachmentUrl)=)(.*?)(&|#|$)/;
            // eslint-disable-next-line no-undef
            const url = encodeURIComponent(window.location.href);

            this.$('a').each((index, element) => {
                const $a = $(element);
                if ($a.hasClass('s_share_snapchat')) {
                    $a.attr('href', (i, href) => {
                        return href.replace(urlRegex, (match, a, b, c) => {
                            return a + url + c;
                        });
                    });
                }
            });
        },
    });
