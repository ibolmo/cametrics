<?php

require_once dirname(__FILE__).'/../clients/php/Cametrics.class.php';

Cametrics::initialize('agljYW1ldHJpY3NyFAsSDm15YXBwX2NhbXBhaWduGAgM');

Cametrics::measure('test');

Cametrics::measure('namespace.value');
#
#Cametrics::measure('namespace.column.number', 10, 'number');
#
#Cametrics::measure('namespace.column.string', 'string value', 'string');

