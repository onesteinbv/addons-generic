=====================
Website Cache Control
=====================

Cache-Control for reverse proxy

Configuration
~~~~~~~~~~~~~

.. code-block::


    proxy_cache_path /etc/nginx/cache/odoo levels=1:2 keys_zone=odoo:10m max_size=10g inactive=60m use_temp_path=off;

    location /web {
        proxy_redirect off;
        proxy_cache off;
        proxy_pass http://odoo;
    }

    location /website_payment {
        proxy_redirect off;
        proxy_cache off;
        proxy_pass http://odoo;
    }

    location /payment {
        proxy_redirect off;
        proxy_cache off;
        proxy_pass http://odoo;
    }

    location /shop {
        proxy_redirect off;
        proxy_cache off;
        proxy_pass http://odoo;
    }

    location /my {
        proxy_redirect off;
        proxy_cache off;
        proxy_pass http://odoo;
    }

     # Redirect requests to odoo backend server
    location / {
        proxy_cache odoo;
        proxy_cache_methods GET HEAD;
        proxy_cache_valid 200 10m;
        proxy_cache_key $host$request_uri$cookie_frontend_lang$cookie_odoo_backend;
        proxy_redirect off;
        proxy_pass http://odoo;
    }


Credits
=======

Contributors
------------

* Dennis Sluijk <d.sluijk@onestein.nl>
* Mark Schuit <mark@gig.solutions>
