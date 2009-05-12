<?php

/*
 * This file is part of the sfWebBrowserPlugin package. 
 * (c) 2004-2006 Francois Zaninotto <francois.zaninotto@symfony-project.com>
 * (c) 2004-2006 Fabien Potencier <fabien.potencier@symfony-project.com> for the click-related functions
 * 
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

/**
 * sfWebBrowser provides a basic HTTP client.
 *
 * @package    sfWebBrowserPlugin
 * @author     Francois Zaninotto <francois.zaninotto@symfony-project.com>
 * @author     Tristan Rivoallan <tristan@rivoallan.net>
 * @version    0.9
 */
class sfWebBrowser
{
  protected
    $defaultHeaders          = array(),
    $stack                   = array(),
    $stackPosition           = -1,
    $responseHeaders         = array(),
    $responseCode            = '',
    $responseMessage         = '',
    $responseText            = '',
    $responseDom             = null,
    $responseDomCssSelector  = null,
    $responseXml             = null,
    $fields                  = array(),
    $urlInfo                 = array();

  public function __construct($defaultHeaders = array(), $adapterOptions = array())
  {
    $this->defaultHeaders = $this->fixHeaders($defaultHeaders);
    $this->adapter = new sfCurlAdapter($adapterOptions);
  }
    
  // Browser methods
  
  /**
   * Restarts the browser
   *
   * @param array default browser options
   *
   * @return sfWebBrowser The current browser object
   */    
  public function restart($defaultHeaders = array())
  {
    $this->defaultHeaders = $this->fixHeaders($defaultHeaders);
    $this->stack          = array();
    $this->stackPosition  = -1;
    $this->urlInfo        = array();
    $this->initializeResponse();
    
    return $this;
  }

  /**
   * Sets the browser user agent name
   *
   * @param string agent name
   *
   * @return sfWebBrowser The current browser object
   */    
  public function setUserAgent($agent)
  {
    $this->defaultHeaders['User-Agent'] = $agent;
    
    return $this;
  }

  /**
   * Gets the browser user agent name
   *
   * @return string agent name
   */    
  public function getUserAgent()
  {
    return isset($this->defaultHeaders['User-Agent']) ? $this->defaultHeaders['User-Agent'] : '';
  }

  /**
   * Submits a GET request
   *
   * @param string The request uri
   * @param array  The request parameters (associative array)
   * @param array  The request headers (associative array)
   *
   * @return sfWebBrowser The current browser object
   */
  public function get($uri, $parameters = array(), $headers = array())
  {
    if ($parameters)
    {
      $uri .= ((false !== strpos($uri, '?')) ? '&' : '?') . http_build_query($parameters, '', '&');
    }
    return $this->call($uri, 'GET', array(), $headers);
  }

  public function head($uri, $parameters = array(), $headers = array())
  {
    if ($parameters)
    {
      $uri .= ((false !== strpos($uri, '?')) ? '&' : '?') . http_build_query($parameters, '', '&');
    }
    return $this->call($uri, 'HEAD', array(), $headers);
  }

  /**
   * Submits a POST request
   *
   * @param string The request uri
   * @param array  The request parameters (associative array)
   * @param array  The request headers (associative array)
   *
   * @return sfWebBrowser The current browser object
   */  
  public function post($uri, $parameters = array(), $headers = array())
  {
    return $this->call($uri, 'POST', $parameters, $headers);
  }
  
  /**
   * Submits a PUT request.
   *
   * @param string The request uri
   * @param array  The request parameters (associative array)
   * @param array  The request headers (associative array)
   *
   * @return sfWebBrowser The current browser object
   */  
  public function put($uri, $parameters = array(), $headers = array())
  {
    return $this->call($uri, 'PUT', $parameters, $headers);
  }

  /**
   * Submits a DELETE request.
   *
   * @param string The request uri
   * @param array  The request parameters (associative array)
   * @param array  The request headers (associative array)
   *
   * @return sfWebBrowser The current browser object
   */  
  public function delete($uri, $parameters = array(), $headers = array())
  {
    return $this->call($uri, 'DELETE', $parameters, $headers);
  }

  /**
   * Submits a request
   *
   * @param string  The request uri
   * @param string  The request method
   * @param array   The request parameters (associative array)
   * @param array   The request headers (associative array)
   * @param boolean To specify is the request changes the browser history
   *
   * @return sfWebBrowser The current browser object
   */  
  public function call($uri, $method = 'GET', $parameters = array(), $headers = array(), $changeStack = true)
  {
    $urlInfo = parse_url($uri);

    // Check headers
    $headers = $this->fixHeaders($headers);

    // check port
    if (isset($urlInfo['port']))
    {
      $this->urlInfo['port'] = $urlInfo['port'];
    }
    else if (!isset($this->urlInfo['port']))
    {
      $this->urlInfo['port'] = 80;
    }

    if(!isset($urlInfo['host']))
    {
      // relative link
      $uri = $this->urlInfo['scheme'].'://'.$this->urlInfo['host'].':'.$this->urlInfo['port'].'/'.$uri;
    }
    else if($urlInfo['scheme'] != 'http' && $urlInfo['scheme'] != 'https')
    {
      throw new Exception('sfWebBrowser handles only http and https requests'); 
    }

    $this->urlInfo = parse_url($uri);

    $this->initializeResponse();

    if ($changeStack)
    {
      $this->addToStack($uri, $method, $parameters, $headers);
    }

    $browser = $this->adapter->call($this, $uri, $method, $parameters, $headers);

    // redirect support
    if ((in_array($browser->getResponseCode(), array(301, 307)) && in_array($method, array('GET', 'HEAD'))) || in_array($browser->getResponseCode(), array(302,303)))
    {
      $this->call($browser->getResponseHeader('Location'), 'GET', array(), $headers);
    }

    return $browser;
  }

  /**
   * Adds the current request to the history stack
   *
   * @param string  The request uri
   * @param string  The request method
   * @param array   The request parameters (associative array)
   * @param array   The request headers (associative array)
   *
   * @return sfWebBrowser The current browser object
   */  
  public function addToStack($uri, $method, $parameters, $headers)
  {
    $this->stack = array_slice($this->stack, 0, $this->stackPosition + 1);
    $this->stack[] = array(
      'uri'        => $uri,
      'method'     => $method,
      'parameters' => $parameters,
      'headers'    => $headers
    );
    $this->stackPosition = count($this->stack) - 1;
    
    return $this;
  }

  /**
   * Submits the previous request in history again
   *
   * @return sfWebBrowser The current browser object
   */  
  public function back()
  {
    if ($this->stackPosition < 1)
    {
      throw new Exception('You are already on the first page.');
    }

    --$this->stackPosition;
    return $this->call($this->stack[$this->stackPosition]['uri'], 
                       $this->stack[$this->stackPosition]['method'], 
                       $this->stack[$this->stackPosition]['parameters'], 
                       $this->stack[$this->stackPosition]['headers'],
                       false);
  }

  /**
   * Submits the next request in history again
   *
   * @return sfWebBrowser The current browser object
   */  
  public function forward()
  {
    if ($this->stackPosition > count($this->stack) - 2)
    {
      throw new Exception('You are already on the last page.');
    }

    ++$this->stackPosition;
    return $this->call($this->stack[$this->stackPosition]['uri'], 
                       $this->stack[$this->stackPosition]['method'], 
                       $this->stack[$this->stackPosition]['parameters'], 
                       $this->stack[$this->stackPosition]['headers'],
                       false);
  }

  /**
   * Submits the current request again
   *
   * @return sfWebBrowser The current browser object
   */  
  public function reload()
  {
    if (-1 == $this->stackPosition)
    {
      throw new Exception('No page to reload.');
    }

    return $this->call($this->stack[$this->stackPosition]['uri'], 
                       $this->stack[$this->stackPosition]['method'], 
                       $this->stack[$this->stackPosition]['parameters'], 
                       $this->stack[$this->stackPosition]['headers'],
                       false);
  }
  
  /**
   * Transforms an associative array of header names => header values to its HTTP equivalent.
   * 
   * @param    array     $headers
   * @return   string
   */
  public function prepareHeaders($headers = array())
  {
    $prepared_headers = array();
    foreach ($headers as $name => $value)
    {
      $prepared_headers[] = sprintf("%s: %s\r\n", ucfirst($name), $value);
    }
    
    return implode('', $prepared_headers);
  }
  
  // Response methods

  /**
   * Initializes the response and erases all content from prior requests
   */  
  public function initializeResponse()
  {
    $this->responseHeaders        = array();
    $this->responseCode           = '';
    $this->responseText           = '';
    $this->responseDom            = null;
    $this->responseDomCssSelector = null;
    $this->responseXml            = null;
    $this->fields                 = array();
  }

  /**
   * Set the response headers
   *
   * @param array The response headers as an array of strings shaped like "key: value"
   *
   * @return sfWebBrowser The current browser object
   */  
  public function setResponseHeaders($headers = array())
  {
    $header_array = array();
    foreach($headers as $header)
    {
      $arr = explode(': ', $header); 
      if(isset($arr[1]))
      {
        $header_array[$this->normalizeHeaderName($arr[0])] = trim($arr[1]);
      }
    }
    
    $this->responseHeaders = $header_array;
    
    return $this;
  }
  
  /**
   * Set the response code
   *
   * @param string The first line of the response
   *
   * @return sfWebBrowser The current browser object
   */  
  public function setResponseCode($firstLine)
  {
    preg_match('/\d{3}/', $firstLine, $matches); 
    $this->responseCode = count($matches) and $matches[0] or 500;    
    return $this;
  }  

  /**
   * Set the response contents
   *
   * @param string The response contents
   *
   * @return sfWebBrowser The current browser object
   */  
  public function setResponseText($res)
  {
    $this->responseText = $res;
    
    return $this;
  }

  /**
   * Get a text version of the response
   *
   * @return string The response contents
   */
  public function getResponseText()
  {
    $text = $this->responseText;

    // Decode any content-encoding (gzip or deflate) if needed
    switch (strtolower($this->getResponseHeader('content-encoding'))) {

        // Handle gzip encoding
        case 'gzip':
            $text = $this->decodeGzip($text);
            break;

        // Handle deflate encoding
        case 'deflate':
            $text = $this->decodeDeflate($text);
            break;

        default:
            break;
    }

    return $text;
  }

  /**
   * Get a text version of the body part of the response (without <body> and </body>)
   *
   * @return string The body part of the response contents
   */
  public function getResponseBody()
  {
    preg_match('/<body.*?>(.*)<\/body>/si', $this->getResponseText(), $matches);

    return $matches[1];
  }
  
  /**
   * Get a DOMDocument version of the response 
   *
   * @return DOMDocument The reponse contents
   */
  public function getResponseDom()
  {
    if(!$this->responseDom)
    {
      // for HTML/XML content, create a DOM object for the response content
      if (preg_match('/(x|ht)ml/i', $this->getResponseHeader('Content-Type')))
      {
        $this->responseDom = new DomDocument('1.0', 'utf8');
        $this->responseDom->validateOnParse = true;
        @$this->responseDom->loadHTML($this->getResponseText());
      }
    }

    return $this->responseDom;
  }

  /**
   * Get a sfDomCssSelector version of the response 
   *
   * @return sfDomCssSelector The response contents
   */
  /*
  public function getResponseDomCssSelector()
  {
    if(!$this->responseDomCssSelector)
    {
      // for HTML/XML content, create a DOM object for the response content
      if (preg_match('/(x|ht)ml/i', $this->getResponseHeader('Content-Type')))
      {
        $this->responseDomCssSelector = new sfDomCssSelector($this->getResponseDom());
      }
    }

    return $this->responseDomCssSelector;
  }
  //*/
  /**
   * Get a SimpleXML version of the response 
   *
   * @return  SimpleXMLElement                      The reponse contents
   * @throws  Exception  when response is not in a valid format 
   */
  public function getResponseXML()
  {
    if(!$this->responseXml)
    {
      // for HTML/XML content, create a DOM object for the response content
      if (preg_match('/(x|ht)ml/i', $this->getResponseHeader('Content-Type')))
      {
        $this->responseXml = @simplexml_load_string($this->getResponseText());
      }
    }
    
    // Throw an exception if response is not valid XML
    if (get_class($this->responseXml) != 'SimpleXMLElement')
    {
      $msg = sprintf("Response is not a valid XML string : \n%s", $this->getResponseText());
      throw new Exception($msg);
    }
    
    return $this->responseXml;
  }

  /**
   * Returns true if server response is an error.
   * 
   * @return   bool
   */
  public function responseIsError()
  {
    return in_array((int)($this->getResponseCode() / 100), array(4, 5)); 
  }

  /**
   * Get the response headers
   *
   * @return array The response headers
   */
  public function getResponseHeaders()
  {
    return $this->responseHeaders;
  }  

  /**
   * Get a response header
   *
   * @param string The response header name
   *
   * @return string The response header value
   */
  public function getResponseHeader($key)
  {
    $normalized_key = $this->normalizeHeaderName($key);
    return (isset($this->responseHeaders[$normalized_key])) ? $this->responseHeaders[$normalized_key] : '';
  }  
  
  /**
   * Decodes gzip-encoded content ("content-encoding: gzip" response header).
   * 
   * @param       stream     $gzip_text
   * @return      string     
   */
  protected function decodeGzip($gzip_text)
  {
    return gzinflate(substr($gzip_text, 10));
  }

  /**
   * Decodes deflate-encoded content ("content-encoding: deflate" response header).
   * 
   * @param       stream     $deflate_text
   * @return      string     
   */  
  protected function decodeDeflate($deflate_text)
  {
    return gzuncompress($deflate_text);
  }
  
  /**
   * Get the response code
   *
   * @return string The response code
   */
  public function getResponseCode()
  {
    return $this->responseCode; 
  }
  
  /**
   * Returns the response message (the 'Not Found' part in  'HTTP/1.1 404 Not Found')
   * 
   * @return   string 
   */
  public function getResponseMessage()
  {
    return $this->responseMessage;    
  }
  
  /**
   * Sets response message.
   * 
   * @param    string    $message
   */
  public function setResponseMessage($msg)
  {
    $this->responseMessage = $msg;
  }
  
  public function getUrlInfo()
  {
    return $this->urlInfo; 
  }
  
  public function getDefaultRequestHeaders()
  {
    return $this->defaultHeaders;
  }
  
  /**
   * Adds default headers to the supplied headers array.
   * 
   * @param       array    $headers
   * @return      array
   */
  public function initializeRequestHeaders($headers = array())
  {
    // Supported encodings
    $encodings = array();
    if (isset($headers['Accept-Encoding']))
    {
      $encodings = explode(',', $headers['Accept-Encoding']);
    }
    if (function_exists('gzinflate'))
    {
      $encodings[] = 'gzip';
    }
    if (function_exists('gzuncompress'))
    {
      $encodings[] = 'deflate';
    }
    
    $headers['Accept-Encoding'] = implode(',', array_unique($encodings));
    
    return $headers;
  }
  
  /**
   * Validates supplied headers and turns all names to lowercase.
   * 
   * @param     array     $headers
   * @return    array
   */
  private function fixHeaders($headers)
  {
    $fixed_headers = array();
    foreach ($headers as $name => $value)
    {
      if (!preg_match('/([a-z]*)(-[a-z]*)*/i', $name))
      {
        $msg = sprintf('Invalid header "%s"', $name);
        throw new Exception($msg);
      }
      $fixed_headers[$this->normalizeHeaderName($name)] = trim($value);
    }

    return $fixed_headers;
  }
  
  /**
   * Retrieves a normalized Header.
   *
   * @param string Header name
   *
   * @return string Normalized header
   */
  protected function normalizeHeaderName($name)
  {
    return preg_replace('/\-(.)/e', "'-'.strtoupper('\\1')", strtr(ucfirst($name), '_', '-'));
  }

  // code from php at moechofe dot com (array_merge comment on php.net)
  /*
   * array arrayDeepMerge ( array array1 [, array array2 [, array ...]] )
   *
   * Like array_merge
   *
   *  arrayDeepMerge() merges the elements of one or more arrays together so
   * that the values of one are appended to the end of the previous one. It
   * returns the resulting array.
   *  If the input arrays have the same string keys, then the later value for
   * that key will overwrite the previous one. If, however, the arrays contain
   * numeric keys, the later value will not overwrite the original value, but
   * will be appended.
   *  If only one array is given and the array is numerically indexed, the keys
   * get reindexed in a continuous way.
   *
   * Different from array_merge
   *  If string keys have arrays for values, these arrays will merge recursively.
   */
  public static function arrayDeepMerge()
  {
    switch (func_num_args())
    {
      case 0:
        return false;
      case 1:
        return func_get_arg(0);
      case 2:
        $args = func_get_args();
        $args[2] = array();
        if (is_array($args[0]) && is_array($args[1]))
        {
          foreach (array_unique(array_merge(array_keys($args[0]),array_keys($args[1]))) as $key)
          {
            $isKey0 = array_key_exists($key, $args[0]);
            $isKey1 = array_key_exists($key, $args[1]);
            if ($isKey0 && $isKey1 && is_array($args[0][$key]) && is_array($args[1][$key]))
            {
              $args[2][$key] = self::arrayDeepMerge($args[0][$key], $args[1][$key]);
            }
            else if ($isKey0 && $isKey1)
            {
              $args[2][$key] = $args[1][$key];
            }
            else if (!$isKey1)
            {
              $args[2][$key] = $args[0][$key];
            }
            else if (!$isKey0)
            {
              $args[2][$key] = $args[1][$key];
            }
          }
          return $args[2];
        }
        else
        {
          return $args[1];
        }
      default :
        $args = func_get_args();
        $args[1] = self::arrayDeepMerge($args[0], $args[1]);
        array_shift($args);
        return call_user_func_array(array('sfWebBrowser', 'arrayDeepMerge'), $args);
        break;
    }
  }

}

/*
 * This file is part of the sfWebBrowserPlugin package.
 * (c) 2004-2006 Francois Zaninotto <francois.zaninotto@symfony-project.com>
 * (c) 2004-2006 Fabien Potencier <fabien.potencier@symfony-project.com> for the click-related functions
 * 
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

/**
 * sfWebBrowser provides a basic HTTP client.
 *
 * @package    sfWebBrowserPlugin
 * @author     Francois Zaninotto <francois.zaninotto@symfony-project.com>
 * @author     Ben Meynell <bmeynell@colorado.edu>
 * @version    0.9
 */

class sfCurlAdapter
{
  protected
    $options = array(),
    $curl    = null,
    $headers = array();

  /**
   * Build a curl adapter instance
   * Accepts an option of parameters passed to the PHP curl adapter:
   *  ssl_verify  => [true/false]
   *  verbose     => [true/false]
   *  verbose_log => [true/false]
   * Additional options are passed as curl options, under the form:
   *  userpwd => CURL_USERPWD
   *  timeout => CURL_TIMEOUT
   *  ...
   *
   * @param array $options Curl-specific options
   */
  public function __construct($options = array())
  {
    if (!extension_loaded('curl'))
    {
      throw new Exception('Curl extension not loaded');
    }

    $this->options = $options;
    $curl_options = $options;
    
    $this->curl = curl_init();
    $cookie_dir = sys_get_temp_dir();
    // cookies
    if (isset($curl_options['cookies']))
    {
      if (isset($curl_options['cookies_file']))
      {
        $cookie_file = $curl_options['cookies_file'];
        unset($curl_options['cookies_file']);
      }
      else
      {
        $cookie_file = $cookie_dir.'/sfWebBrowserPlugin/sfCurlAdapter/cookies.txt';
      }
      if (isset($curl_options['cookies_dir']))
      {
        $cookie_dir = $curl_options['cookies_dir'];
        unset($curl_options['cookies_dir']);
      }
      else
      {
        $cookie_dir .= '/sfWebBrowserPlugin/sfCurlAdapter';
      }
      if (!is_dir($cookie_dir))
      {
        if (!mkdir($cookie_dir, 0777, true))
        {
          throw new Exception(sprintf('Could not create directory "%s"', $cookie_dir));
        }
      }

      curl_setopt($this->curl, CURLOPT_COOKIESESSION, false);
      curl_setopt($this->curl, CURLOPT_COOKIEJAR, $cookie_file);
      curl_setopt($this->curl, CURLOPT_COOKIEFILE, $cookie_file);
      unset($curl_options['cookies']);
    }

    // default settings
    curl_setopt($this->curl, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($this->curl, CURLOPT_AUTOREFERER, true);
    curl_setopt($this->curl, CURLOPT_FOLLOWLOCATION, false);
    curl_setopt($this->curl, CURLOPT_FRESH_CONNECT, true);
    
    if(isset($this->options['followlocation']))
    {
      curl_setopt($this->curl, CURLOPT_FOLLOWLOCATION, (bool) $this->options['followlocation']);
    }
    
    // activate ssl certificate verification?
    
    if (isset($this->options['ssl_verify_host']))
    {
      curl_setopt($this->curl, CURLOPT_SSL_VERIFYHOST, (bool) $this->options['ssl_verify_host']);
    }
    if (isset($curl_options['ssl_verify']))
    {
      curl_setopt($this->curl, CURLOPT_SSL_VERIFYPEER, (bool) $this->options['ssl_verify']);
      unset($curl_options['ssl_verify']);
    }
    // verbose execution?
    if (isset($curl_options['verbose']))
    {
      curl_setopt($this->curl, CURLOPT_NOPROGRESS, false);
      curl_setopt($this->curl, CURLOPT_VERBOSE, true);
      unset($curl_options['cookies']);
    }
    if (isset($curl_options['verbose_log']))
    {
      $log_file = sfConfig::get('sf_log_dir').'/sfCurlAdapter_verbose.log';
      curl_setopt($this->curl, CURLOPT_VERBOSE, true);
      $this->fh = fopen($log_file, 'a+b');
      curl_setopt($this->curl, CURLOPT_STDERR, $this->fh);
      unset($curl_options['verbose_log']);
    }
    
    // Additional options
    foreach ($curl_options as $key => $value)
    {
      $const = constant('CURLOPT_' . strtoupper($key));
      if(!is_null($const))
      {
        curl_setopt($this->curl, $const, $value);
      }
    }
    
    // response header storage - uses callback function
    curl_setopt($this->curl, CURLOPT_HEADERFUNCTION, array($this, 'read_header'));
  }

  /**
   * Submits a request
   *
   * @param string  The request uri
   * @param string  The request method
   * @param array   The request parameters (associative array)
   * @param array   The request headers (associative array)
   *
   * @return sfWebBrowser The current browser object
   */
  public function call($browser, $uri, $method = 'GET', $parameters = array(), $headers = array())
  {
    // uri
    curl_setopt($this->curl, CURLOPT_URL, $uri);

    // request headers
    $m_headers = array_merge($browser->getDefaultRequestHeaders(), $browser->initializeRequestHeaders($headers));
    $request_headers = explode("\r\n", $browser->prepareHeaders($m_headers));
    curl_setopt($this->curl, CURLOPT_HTTPHEADER, $request_headers);
   
    // encoding support
    if(isset($headers['Accept-Encoding']))
    {
      curl_setopt($this->curl, CURLOPT_ENCODING, $headers['Accept-Encoding']);
    }
    
    // timeout support
    if(isset($this->options['Timeout']))
    {
      curl_setopt($this->curl, CURLOPT_TIMEOUT, $this->options['Timeout']);
    }
    
    if (!empty($parameters))
    {
      if (!is_array($parameters))
      {
        curl_setopt($this->curl, CURLOPT_POSTFIELDS, $parameters);
      }
      else
      {
        // multipart posts (file upload support)
        $has_files = false;
        foreach ($parameters as $name => $value)
        {
          if (is_array($value)) {
            continue;
          }
          if (is_file($value))
          {
            $has_files = true;
            $parameters[$name] = '@'.realpath($value);
          }
        }
        if($has_files)
        {
          curl_setopt($this->curl, CURLOPT_POSTFIELDS, $parameters);
        }
        else
        {
          curl_setopt($this->curl, CURLOPT_POSTFIELDS, http_build_query($parameters, '', '&'));
        }
      }
    }

    // handle any request method
    curl_setopt($this->curl, CURLOPT_CUSTOMREQUEST, $method);

    $response = curl_exec($this->curl);

    if (curl_errno($this->curl))
    {
      throw new Exception(curl_error($this->curl));
    }

    $requestInfo = curl_getinfo($this->curl);

    $browser->setResponseCode($requestInfo['http_code']);
    $browser->setResponseHeaders($this->headers);
    $browser->setResponseText($response);

    // clear response headers
    $this->headers = array();

    return $browser;
  }

  public function __destroy()
  {
    curl_close($this->curl);
  }

  protected function read_header($curl, $headers)
  {
    $this->headers[] = $headers;
    
    return strlen($headers);
  }
}
