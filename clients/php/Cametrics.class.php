<?php

/*
    Cametrics::measure('visitor',
*/

class Cametrics
{
    private $instance = null;
    public $options = array(
        
    );
    
    function __construct($options = array())
    {
        $this->setOptions($options);
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
    
    public static measure($namespace, $value = 1, $type = 'number')
    {
        $instance = self::getInstance();
    }
}
