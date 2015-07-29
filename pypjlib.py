class payjunctionrestlib:
    """ A library containing classes for processing requests on the PayJunction REST API
        Version: 0.1.0.dev
    """
    
    
    import json
    from exceptions import ValueError, KeyError, TypeError
    
    # Constants for API endpoints
    TRANSACTIONS = "/transactions/"
    CUSTOMERS = "/customers/"
    NOTES = "{}/notes/" # All note queries requires the either the customer id or the transaction id, therefore this must be used with a format($cust_id|$txn_id)
    RECEIPTS = "{}/receipts/latest/" # All receipt queries requires the transaction id, therefore this must be used with a format($txn_id)
    RECEIPTS_THERMAL = "{}/receipts/latest/thermal" # All receipt queries requires the transaction id, therefore this must be used with a format($txn_id)
    RECEIPTS_FULLPAGE = "{}/receipts/latest/fullpage" # All receipt queries requires the transaction id, therefore this must be used with a format($txn_id)
    EMAIL_RECEIPT = "{}/receipts/latest/email" # All receipt queries requires the transaction id, therefore this must be used with a format($txn_id)
    ADDRESSES = "{}/addresses/" # All address queries requires the customer id, therefore this must be used with a format($cust_id)
    VAULTS = "{}/vaults/" # All vault queries requires the customer id, therefore this must be used with a format($cust_id)
    
    # Constants for verify functions
    SWIPE_REQUIRED = ("cardSwipe", "amountBase")
    KEY_REQUIRED = ("cardNumber", "cardExpMonth", "cardExpYear", "amountBase")
    ACH_REQUIRED = ("achRoutingNumber", "achAccountNumber", "achAccountType", "achType", "amountBase")
    REQ_LIST = {'swipe': SWIPE_REQUIRED, 'key': KEY_REQUIRED, 'ach': ACH_REQUIRED}
    
    __login = ""
    __password = ""
    __app_key = ""
    __test = False
    
    def __init__(self, login, passwd, key, test=False):
        self.__login = login
        self.__password = passwd
        self.__app_key = key
        self.__test = test
        
    def verify(self, to_test, vtype):
        for key in self.REQ_LIST[vtype]:
            if key not in to_test:
                raise KeyError(key + " is a required parameter for this transaction type.")
            if not to_test[key]:
                raise ValueError(key + " cannot be empty or None.")
            
    def __process(self, ptype, method, data=None):
        import requests
        
        headers = {"X-PJ-Application-Key" : self.__app_key}
        auth = requests.auth.HTTPBasicAuth(self.__login, self.__password)
        
        url = ""
        if (self.__test == False):
            url = "https://api.payjunction.com"
        else:
            url = "https://api.payjunctionlabs.com"
        
        url += ptype
        
        if (method == 'post'):
            r = requests.post(url=url, data=data, auth=auth, headers=headers)
        elif (method == 'put'):
            r = requests.put(url=url, data=data, auth=auth, headers=headers)
        elif (method == 'get'):
            r = requests.get(url=url, auth=auth, headers=headers)
        elif (method == 'delete'):
            r = requests.delete(url=url, auth=auth, headers=headers)
        else:
            raise ValueError("the method parameter must be either 'post', 'put', 'get' or 'delete'")
            
        if (r.status_code == requests.codes.ok):
            json_response = r.json()
            raw_response = r.text
            r = None # Make sure GC clears the memory with the card and authentication info in it as soon as possible
            return (json_response, raw_response)
        else:
            r.request = None # Make sure GC clears the memory with the card and authentication info in it as soon as possible
            r.raise_for_status()
    
    def post(self, ptype, data):
        return self.__process(ptype, 'post', data)
    
    def put(self, ptype, data):
        return self.__process(ptype, 'put', data)
        
    def get(self, ptype):
        return self.__process(ptype, 'get')
    
    def delete(self, ptype):
        return self.__process(ptype, 'delete')
        
    def enable_test_mode(self):
        self.__test == True
    
    def disable_test_mode(self):
        self.__test == False
    
    def create_transaction(self, params):
         # Verify we have the required parameters for the transaction type
        if 'cardNumber' in params:
            #Verify we have all required fields for a keyed transaction
            self.verify(params, 'key')
                
        elif 'cardTrack' in params:
            self.verify(params, 'swipe')
                    
        elif 'achRoutingNumber' in params:
            self.verify(params, 'ach')
        
        else:
            raise ValueError('A valid transaction request needs either cardNumber, cardTrack, or achRoutingNumber defined in the parameters to be valid')
        
        r = self.post(self.TRANSACTIONS, params)
        
        return payjunctionrestlib.Transaction(self, r[0], r[1])
    
    def get_transaction(self, txn_id):
        if txn_id is None or txn_id == "": raise ValueError("A valid transactionId is needed to use get_transaction()")
        r = self.get(self.TRANSACTIONS + txn_id)
        return payjunctionrestlib.Transaction(self, r[0], r[1])
        
        
    class Transaction(object):
        
        #Constants for use with create()
        KEYED = 'key'
        SWIPED = 'swipe'
        ACH = 'ach'
        
        __hook = None
        #__notes = []
        #__receipts = None
        __transaction_id = 0
        __uri = ""
        __terminal_id = 0
        __action = ""
        __amount_base = 0.00
        __amount_tax = 0.00
        __amount_shipping = 0.00
        __amount_tip = 0.00
        __amount_surcharge = 0.00
        __amount_reject = 0.00
        __amount_total = 0.00
        __invoice_number = ""
        __purchase_order_number = ""
        __status = ""
        __created = None
        __last_mod = None
        __response = {
            "approved": None,
            "code": "",
            "message": "",
            "processor": {
                "authorized": None,
                "approvalCode": "",
                "avs": {
                   "status": "",
                   "requested": "",
                   "match": {
                       "ZIP": None,
                       "ADDRESS": None
                   }
                },
                "cvv": ""
            }
        }
       
        __settlement = None
        __vault = None
        
        """{
            "type" : "",
            "acocuntType": "",
            "lastFour": ""
            }"""

        __billing = None
        
        """{
            "firstName": "",
            "middleName": "",
            "lastName": "",
            "companyName": "",
            "email": "",
            "phone": "",
            "phone2": "",
            "jobTitle": "",
            "identifier": "",
            "website": "",
            "address": {
                "address": "",
                "city": "",
                "state": "",
                "country": "",
                "zip": ""
            }
        }"""
        __shipping = None
        
        """{
            "firstName": "",
            "middleName": "",
            "lastName": "",
            "companyName": "",
            "email": "",
            "phone": "",
            "phone2": "",
            "jobTitle": "",
            "identifier": "",
            "website": "",
            "address": {
                "address": "",
                "city": "",
                "state": "",
                "country": "",
                "zip": ""
            }
        }"""
        __json = ""
        
        def __init__(self, hook, r_dict, js):
            self.__hook = hook
            #self.__notes = notes
            #self.__receipts = receipts
            self.__transaction_id = r_dict['transactionId']
            self.__uri = r_dict['uri']
            self.__terminal_id = r_dict['terminalId']
            self.__action = r_dict['action']
            self.__amount_base = r_dict['amountBase']
            if 'amountTax' in r_dict: self.__amount_tax = r_dict['amountTax']
            if 'amountShipping' in r_dict: self.__amount_shipping = r_dict['amountShipping']
            if 'amountTip' in r_dict: self.__amount_tip = r_dict['amountTip']
            if 'amountSurcharge' in r_dict: self.__amount_surcharge = r_dict['amountSurcharge']
            if 'amountReject' in r_dict: self.__amount_reject = r_dict['amountReject']
            self.__amount_total = r_dict['amountTotal']
            if 'invoiceNumber' in r_dict: self.__invoice_number = r_dict['invoiceNumber']
            if 'purchaseOrderNumber' in r_dict: self.__purchase_order_number = r_dict['purchaseOrderNumber']
            self.__status = r_dict['status']
            self.__created = r_dict['created']
            self.__last_mod = r_dict['lastModified']
            if 'response' in r_dict: self.__response = r_dict['response']
            if 'settlement' in r_dict: self.__settlement = r_dict['settlement']
            if 'vault' in r_dict: self.__vault = r_dict['vault']
            if 'billing' in r_dict: self.__billing = r_dict['billing']
            if 'shipping' in r_dict: self.__shipping = r_dict['shipping']
            self.__json = js
        
        def __get_dict(self):
            txn_dict = {'status': self.__status, 'amountBase': self.__amount_base, 'amountTax': self.__amount_tax, 'amountShipping': self.__amount_shipping, 'amountTip': self.__amount_tip}
            if self.__vault is not None:
                if self.__vault['type'] is "ACH": txn_dict['amountReject'] = self.__amount_reject
            if self.__invoice_number is not "": txn_dict['invoiceNumber'] = self.__invoice_number
            if self.__purchase_order_number is not "": txn_dict['purchaseOrderNumber'] = self.__purchase_order_number
            if self.__billing is not None:
                b = self.__billing
                if 'firstName' in b: txn_dict['billingFirstName'] = b['firstName']
                if 'lastName' in b: txn_dict['billingLastName'] = b['lastName']
                if 'companyName' in b: txn_dict['billingCompanyName'] = b['companyName']
                if 'email' in b: txn_dict['billingEmail'] = b['email']
                if 'phone' in b: txn_dict['billingPhone'] = b['phone']
                if 'phone2' in b: txn_dict['billingPhone2'] = b['phone2']
                if 'jobTitle' in b: txn_dict['billingJobTitle'] = b['jobTitle']
                if 'identifier' in b: txn_dict['billingIdentifier'] = b['identifier']
                if 'website' in b: txn_dict['billingWebsite'] = b['website']
                if 'address' in b:
                    a = b['address']
                    if 'address' in a: txn_dict['billingAddress'] = a['address']
                    if 'city' in a: txn_dict['billingCity'] = a['city']
                    if 'state' in a: txn_dict['billingState'] = a['state']
                    if 'country' in a: txn_dict['billingCountry'] = a['country']
                    if 'zip' in a: txn_dict['billingZip'] = a['zip']
            if self.__shipping is not None:
                b = self.__shipping
                if 'firstName' in b: txn_dict['shippingFirstName'] = b['firstName']
                if 'lastName' in b: txn_dict['shippingLastName'] = b['lastName']
                if 'companyName' in b: txn_dict['shippingCompanyName'] = b['companyName']
                if 'email' in b: txn_dict['shippingEmail'] = b['email']
                if 'phone' in b: txn_dict['shippingPhone'] = b['phone']
                if 'phone2' in b: txn_dict['shippingPhone2'] = b['phone2']
                if 'jobTitle' in b: txn_dict['shippingJobTitle'] = b['jobTitle']
                if 'identifier' in b: txn_dict['shippingIdentifier'] = b['identifier']
                if 'website' in b: txn_dict['shippingWebsite'] = b['website']
                if 'address' in b:
                    a = b['address']
                    if 'address' in a: txn_dict['shippingAddress'] = a['address']
                    if 'city' in a: txn_dict['shippingCity'] = a['city']
                    if 'state' in a: txn_dict['shippingState'] = a['state']
                    if 'country' in a: txn_dict['shippingCountry'] = a['country']
                    if 'zip' in a: txn_dict['shippingZip'] = a['zip']
            
            
            return txn_dict
                    
        
        def update(self):
            if self.__hook is not None:
                self.__hook.put(payjunctionrestlib.TRANSACTIONS + self.__transaction_id, self.__get_dict())
            else:
                raise TypeError("The payjunctionrestlib object is no longer available")
            
        def recharge(self, amount=None):
            #TODO
            pass
            
        def void(self):
            #TODO
            pass
            
        def refund(self):
            #TODO
            pass
        
        def get_transaction_id(self):
            return self.__transaction_id
        
        def get_amounts(self):
            return {'amountBase': self.__amount_base, 'amountTax': self.__amount_tax, 'amountShipping': self.__amount_shipping, 
                    'amountTip': self.__amount_tip, 'amountReject': self.__amount_reject, 'amountTotal': self.__amount_total}
        
        def set_amounts(self, a_dict):
            if 'amountBase' in a_dict: self.__amount_base = a_dict['amountBase']
            if 'amountTax' in a_dict: self.__amount_tax = a_dict['amountTax']
            if 'amountShipping' in a_dict: self.__amount_shipping = a_dict['amountShipping']
            if 'amountTip' in a_dict: self.__amount_tip = a_dict['amountTip']
            if 'amountReject' in a_dict:
                if self.__vault is not None and self.__vault['type'] is "ACH":
                    self.__amount_reject = a_dict['amountReject']
                else:
                    raise ValueError("Cannot set an amountReject on this transaction")
                    
            
    class Note(object):
        
        __note_id = None
        __uri = None
        text = None
        __created = None
        __last_mod = None
        __user = None
        
        def __init__(self, n_id, uri, text, created, lm, user):
            self.__note_id = n_id
            self.__uri = uri
            self.text = text
            self.__created = created
            self.__last_mod = lm
            self.__user = user
        
        def create(self, note):
            #TODO
            pass
        
        def get(self, n_id):
            #TODO
            pass
        
        def note_id(self):
            return self.__note_id
        
        def uri(self):
            return self.__uri
        
        def created(self):
            return self.__created
        
        def last_modified(self):
            return self.__last_mod
        
        def user(self):
            return self.__user
        
    class  Receipts(object):
        
        __uri = ""
        __sig_status = ""
        __terms = 0.00
        __sig_current = False
        __signature = {"signedBy" : "",
                        "dateSigned" : None,
                        "source" : "",
                        "device" : "",
                        "deviceVersion" : "",
                        "image" : ""}
        __documents = {"thermal" : "",
                       "fullpage" : ""}
        __actions = {"email" : ""}
        __created = None
        __last_mod = None
        
        def __init__(self, uri, ss, terms, sc, sig, docs, act, created, lm):
            self.__uri = uri
            self.__sig_status = ss
            self.__terms = terms
            self.__sig_current = sc
            self.__signature = sig
            self.__documents = docs
            self.__actions = act
            self.__created = created
            self.__last_mod = lm
        
        def get(self, transaction_id):
            #TODO
            pass
        
        def add_signature(self, raw):
            #TODO
            pass
        
        def uri(self):
            return self.__uri
            
        def signature_status(self):
            return self.__sig_status
        
        def signature(self):
            return self.__signature
            
        def documents(self):
            return self.__documents
            
        def actions(self):
            return self.__actions
        
        def created(self):
            return self.__created
            
        def last_modified(self):
            return self.__last_mod
        
    class Customer(object):
        
        __instance = None
        __customer_id = None
        __uri = None
        first_name = None
        last_name = None
        company_name = None
        email = None
        phone = None
        phone2 = None
        job_title = None
        identifier = None
        website = None
        custom1 = None
        __created = None
        __last_mod = None
        __addresses = None
        __default_address = None
        __vaults = None
        
        def __init__(self, instance, c_id, uri, first, last, company, email, phone, phone2, job, ident, web, custom, created, lm, addresses, default, vaults):
            self.__instance = instance
            self.__customer_id = c_id
            self.__uri = uri
            self.first_name = first
            self.last_name = last
            self.company_name = company
            self.email = email
            self.phone = phone
            self.phone2 = phone2
            self.job_title = job
            self.identifier = ident
            self.website = web
            self.custom1 = custom
            self.__created = created
            self.__last_mod = lm
            self.__addresses = addresses
            self.__default_address = default
            self.__vaults = vaults
        
        def create(self, first="", last="", company="", email="", phone="", phone2="", job="", web="", custom=""):
            #TODO
            pass
        
        def get(self, id):
            #TODO
            pass
        
        def update(self):
            #TODO
            pass
        
        def customer_id(self):
            return self.__customer_id
        
        def uri(self):
            return self.__uri
        
        def created(self):
            return self.__created
        
        def last_modified(self):
            return self.__last_mod
        
        def addresses(self):
            return self.__addresses
            
        def default_address(self):
            return self.__default_address
        
        def vaults(self):
            return self.__vaults
            
    class Address(object):
        
        __address_id = None
        __uri = None
        address = None
        city = None
        state = None
        country = None
        zip = None
        __created = None
        __last_mod = None
        
        def __init__(self, a_id, uri, add, city, state, ctry, zip, created, lm):
            self.__address_id = a_id
            self.__uri = uri
            self.address = add
            self.city = city
            self.state = state
            self.country = ctry
            self.zip = zip
            self.__created = created
            self.__last_mod = lm
            
        def create(self, add="", city="", state="", ctry="", zip=""):
            #TODO
            pass
        
        def get(self, id):
            #TODO
            pass
        
        def address_id(self):
            return self.__address_id
        
        def uri(self):
            return self.__uri
        
        def created(self):
            return self.__created
        
        def last_modified(self):
            return self.__last_mod
    
    class Vault(object):
        __vault_id = None
        __uri = None
        __type = None
        __account_type = None
        __last_four = None
        __created = None
        __last_mod = None
        
        def __init__(self, v_id, uri, type, a_type, l4, created, lm):
            self.__vault_id = v_id
            self.__uri = uri
            self.__type = type
            self.__last_four = l4
            self.__created = created
            self.__last_mod = lm
        
        def get(self, id):
            #TODO
            pass
        
        def vault_id(self):
            return self.__vault_id
        
        def uri(self):
            return self.__uri
        
        def type(self):
            return self.__type
        
        def account_type(self):
            return self.__account_type
        
        def last_four(self):
            return self.__last_four
        
        def last_modified(self):
            return self.__last_mod
        
    class Card_Vault(Vault):
        
        __instance = None
        card_exp_month = None
        card_exp_year = None
        address = None
        
        def __init__(self, instance, v_id, uri, type, a_type, l4, created, lm, cem, cey, add):
            super(Card_Vault, self).__init__(v_id, uri, type, a_type, l4, created, lm)
            self.__instance = instance
            self.card_exp_month = cem
            self.card_exp_year = cey
            self.address = add
        
        def update(self):
            #TODO
            pass
        
        def create_swipe(self, swipe):
            #TODO
            pass
        def create_keyed(self, acc_num, cem, cey):
            #TODO
            pass
        
    class ACH_Vault(Vault):
        
        routing_number = None
        ach_type = None
        
        def __init__(self, v_id, uri, type, a_type, l4, created, lm, rn, at):
            super(ACH_Vault, self).__init__(self, v_id, uri, type, a_type, l4, created, lm)
            self.routing_number = rn
            self.ach_type = at
            
        def create(self, ach_route, ach_number, ach_account_type, ach_type):
            #TODO
            return