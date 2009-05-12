<?php

require_once 'sfWebBrowser.class.php';

class Cametrics
{
    private static $instance = null;
    public $options = array(
        'secret.key' => 'agljYW1ldHJpY3NyFAsSDm15YXBwX2NhbXBhaWduGAgM',
        'url.protocol' => 'http',
        'url.host' => 'localhost',
        'url.pattern' => '%s/%s/%s',
        'namespace.separators' => '/[^\w]+/',
    );
    
    function __construct($options = array())
    {
        $this->setOptions($options);
        $this->browser = new sfWebBrowser();
    }
    
    public function initialize($key, $options = array())
    {
        $options['secret.key'] = $key;
        return self::getInstance($options);
    }
    
    public function setOptions($options)
    {
        $this->options = array_merge($this->options, $options);
    }
    
    public static function getInstance($options = array())
    {
        if (!self::$instance) self::$instance = new Cametrics($options);
        return self::$instance;
    }
    
    public static function measure($namespace, $value = 1, $type = 'number')
    {
        self::getInstance()->post($namespace, $value, $type);
    }
    
    public function post($namespace, $value, $type)
    {
        $uri = "{$this->options['url.protocol']}://{$this->options['url.host']}/{$this->options['url.pattern']}";
        $uri = vsprintf($uri, array($this->options['secret.key'], $this->mapNamespace($namespace), $value));
        syslog(LOG_NOTICE, sprintf('Cametrics posting: %s', $uri));
        
        $this->browser->post($uri, array(
            'type' => $type
        ));
        
        $message = sprintf('Cametrics post of: %s, returned %s', $uri, $this->browser->getResponseText());
        switch ($this->browser->getResponseCode()) {
            case 200:
                syslog(LOG_INFO, $message);
                return true;
            
            default:
                # ..
                syslog(LOG_ERR, $message);
                return false;
        }
    }
    
    public function mapNamespace($namespace = '')
    {
        return preg_replace($this->options['namespace.separators'], '/', $namespace);
    }
}
