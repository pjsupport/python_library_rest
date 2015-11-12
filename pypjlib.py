class payjunctionrestlib:
    """ A library containing classes for processing requests on the PayJunction REST API
        Version: 0.1.2.dev
    """
    
    
    import json
    from exceptions import ValueError, KeyError, TypeError, RuntimeError
    
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
    
    # Other Constants
    CONTACT_PARAMS = ('firstname', 'middleName', 'lastName', 'companyName', 'email', 'phone', 'phone2', 'jobTitle', 'identifier', 'website')
    ADDR_PARAMS = ('address', 'city', 'state', 'country', 'zip')
    BILLING_CONV = {'firstName': 'billingFirstName', 'middleName': 'billingMiddleName', 'lastName': 'billingLastName', 'jobTitle': 'billingJobTitle', 
                    'companyName': 'billingCompanyName', 'phone': 'billingPhone', 'phone2': 'billingPhone2', 'address': 'billingAddress', 
                    'city': 'billingCity', 'state': 'billingState', 'zip': 'billingZip', 'country': 'billingCountry', 'email': 'billingEmail', 
                    'website': 'billingWebsite'}
    
    SHIPPING_CONV = {'website': 'shippingWebsite', 'city': 'shippingCity', 'zip': 'shippingZip', 'firstName': 'shippingFirstName', 
                     'companyName': 'shippingCompanyName', 'phone2': 'shippingPhone2', 'jobTitle': 'shippingJobTitle', 'lastName': 'shippingLastName', 
                     'middleName': 'shippingMiddleName', 'phone': 'shippingPhone', 'state': 'shippingState', 'address': 'shippingAddress', 
                     'country': 'shippingCountry', 'email': 'shippingEmail'}
    
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
        
        elif 'transactionId' in params or 'vaultId' in params:
            pass
        else:
            raise ValueError('A valid transaction request needs either cardNumber, cardTrack, or achRoutingNumber defined in the parameters to be valid')
        
        r = self.post(self.TRANSACTIONS, params)
        
        return payjunctionrestlib.Transaction(self, r[0], r[1])
    
    def get_transaction(self, txn_id):
        if txn_id is None or txn_id is "": raise ValueError("A valid transactionId is needed to use get_transaction()")
        r = self.get(self.TRANSACTIONS + txn_id)
        return payjunctionrestlib.Transaction(self, r[0], r[1])
        
    
        
    class Transaction(object):
        
        # Constants for use with create()
        KEYED = 'key'
        SWIPED = 'swipe'
        ACH = 'ach'
        
        # Transaction class specific constants
        STATUS = ("HOLD", "CAPTURE", "VOID")
        ACTION = ("CHARGE", "REFUND")
        AVS = ("ADDRESS", "ZIP", "ADDRESS_AND_ZIP", "ADDRESS_OR_ZIP", "BYPASS", "OFF")
        CVV = ("ON", "OFF")
        ACH_TYPE = ("PPD", "CCD", "TEL")
        AMOUNTS = ("amountBase", "amountTax", "amountShipping", "amountTip", "amountSurcharge", "amountReject")
        
        __is_synced = True
        __hook = None
        #__notes = []
        #__receipts = None
        __transaction_id = 0
        __uri = ""
        __terminal_id = 0
        __ach_type = ""
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
        __response = None
        __settlement = None
        __vault = None
        __billing = None
        __shipping = None
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
            if 'achType' in r_dict: self.__ach_type = r_dict['achType']
            self.__json = js
        
        def __get_dict(self):
            txn_dict = {'status': self.__status, 'amountBase': self.__amount_base, 'amountTax': self.__amount_tax, 'amountShipping': self.__amount_shipping, 'amountTip': self.__amount_tip}
            if self.__vault is not None:
                if self.__vault['type'] is "ACH": 
                    txn_dict['amountReject'] = self.__amount_reject
                    txn_dict['achType'] = self.__ach_type
            if self.__invoice_number is not "": txn_dict['invoiceNumber'] = self.__invoice_number
            if self.__purchase_order_number is not "": txn_dict['purchaseOrderNumber'] = self.__purchase_order_number
            if self.__billing is not None:
                bc = payjunctionrestlib.BILLING_CONV 
                b = self.__billing
                for param in bc:
                    if param in b or param in b['address']: txn_dict[bc[param]] = b[param]
                
            if self.__shipping is not None:
                sc = payjunctionrestlib.SHIPPING_CONV
                s = self.__shipping
                for param in sc:
                    if param in s or param in s['address']: txn_dict[sc[param]] = s[param]
                    
            return txn_dict
                    
        
        def update(self):
            if self.__hook is not None:
                self.__hook.put(payjunctionrestlib.TRANSACTIONS + self.__transaction_id, self.__get_dict())
                self.__is_synced = True
            else:
                raise TypeError("The payjunctionrestlib object is no longer available")
            
        def recharge(self, amount={}):
            if self.__hook is not None:
                d_dict = {"transactionId": self.__transaction_id} 
                if len(amount) > 0:
                    for key in amount:
                        d_dict[key] = amount[key]
                return self.__hook.create_transaction(d_dict)
            else:
                raise TypeError("The payjunctionrestlib object is no longer available")
                
        def void(self):
            self.__status = "VOID"
            self.update()
                
        def refund(self, amount={}):
            if self.__hook is not None:
                d_dict = {"transactionId": self.__transaction_id, "action": "REFUND"}
                if len(amount):
                    for key in amount:
                        d_dict[key] = amount[key]
                return self.__hook.create_transaction(d_dict)
            else:
                raise TypeError("The payjunctionrestlib object is no longer available")
        
        def get_transaction_id(self):
            return self.__transaction_id
        
        def amount_check(self, amount):
            if type(amount) is type("") or type(amount) is type(1) or type(amount) is type(1.00):
                return True
            else:
                raise ValueError("Amount must be of type string, integer or float. You submitted a {} object".format(type(amount)))
        
        def get_amounts(self):
            return {'amountBase': self.__amount_base, 'amountTax': self.__amount_tax, 'amountShipping': self.__amount_shipping, 
                    'amountTip': self.__amount_tip, 'amountReject': self.__amount_reject, 'amountTotal': self.__amount_total}
        
        def set_amounts(self, a_dict):
            for key in a_dict:
                # This will raise an exception if it doesn't pass
                self.amount_check(a_dict[key])
            self.__is_synced = False
            if 'amountBase' in a_dict: self.__amount_base = a_dict['amountBase']
            if 'amountTax' in a_dict: self.__amount_tax = a_dict['amountTax']
            if 'amountShipping' in a_dict: self.__amount_shipping = a_dict['amountShipping']
            if 'amountTip' in a_dict: self.__amount_tip = a_dict['amountTip']
            if 'amountReject' in a_dict:
                if self.__vault is not None and self.__vault['type'] is "ACH":
                    self.__amount_reject = a_dict['amountReject']
                else:
                    raise ValueError("Cannot set an amountReject on this transaction")
        
        def get_amount_base(self):
            return self.__amount_base
            
        def set_amount_base(self, amount):
            if self.amount_check(amount): 
                self.__amount_base = amount
                self.__is_synced = False
            
        def get_amount_tax(self):
            return self.__amount_tax
            
        def set_amount_tax(self, amount):
            if self.amount_check(amount): 
                self.__amount_tax = amount
                self.__is_synced = False
        
        def get_amount_shipping(self):
            return self.__amount_shipping
        
        def set_amount_shipping(self, amount):
            if self.amount_check(amount): 
                self.__amount_shipping = amount
                self.__is_synced = False
        
        def get_amount_tip(self):
            return self.__amount_tip
            
        def set_amount_tip(self, amount):
            if self.amount_check(amount): 
                self.__amount_tip = amount
                self.__is_synced = False
        
        def get_amount_reject(self):
            return self.__amount_reject
            
        def set_amount_reject(self, amount):
            if self.amount_check(amount) and self.__vault['type'] is "ACH": 
                self.__amount_reject = amount
                self.__is_synced = False
        def get_status(self):
            return self.__status
        
        def set_status(self, status):
            if status.upper() in self.STATUS and not self.__settlement['settled']:
                self.__status = status
                self.__is_synced = False
        
        def get_ach_type(self):
            return self.__ach_type
        
        def set_ach_type(self, ach_type):
            if self.__vault['type'] is "ACH":
                if ach_type.upper() in self.ACH_TYPE:
                    self.__ach_type = ach_type
                    self.__is_synced = False
                else:
                    raise ValueError("The ACH type must be one of the following: " + ", ".join(self.ACH_TYPE))
            else:
                raise RuntimeError("Cannot set an ACH type on a non-ACH transaction")
        
        def get_billing_info(self):
            return self.__billing
        
        def set_billing_info(self, b_dict):
            for param in payjunctionrestlib.CONTACT_PARAMS:
                if param in b_dict: self.__billing[param] = b_dict[param]
            for param in payjunctionrestlib.ADDR_PARAMS:
                if param in b_dict: self.__billing['address'][param] = b_dict[param]
            self.__is_synced = False
            
        def get_shipping_info(self):
            return self.__shipping
            
        def set_shipping_info(self, s_dict):
            for param in payjunctionrestlib.CONTACT_PARAMS:
               if param in s_dict: self.__shipping[param] = s_dict[param]
            for param in payjunctionrestlib.ADDR_PARAMS:
               if param in s_dict: self.__shipping['address'][param] = s_dict[param]
            self.__is_synced = False
        
        def get_notes(self):
            if self.__hook is not None:
                n_list = [];
                notes = self.__hook.get(payjunctionrestlib.TRANSACTIONS + payjunctionrestlib.NOTES.format(self.__transaction_id))
                for note in notes:
                    n_list.append(payjunctionrestlib.Note(note['noteId'], note['uri'], note['note'], note['created'], note['lastModified'], note['user']))
                return n_list
            else:
                raise TypeError("The payjunctionrestlib object is no longer available")
        
        def add_note(self, note):
            if self.__hook is not None:
                self.__hook.post(payjunctionrestlib.TRANSACTIONS + payjunctionrestlib.NOTES.format(self.__transaction_id), {'note': note})
            else:
                raise TypeError("The payjunctionrestlib object is no longer available")
         
        def get_receipts(self):
            if self.__hook is not None:
                receipts = self.__hook.get(payjunctionrestlib.TRANSACTIONS + payjunctionrestlib.RECEIPTS.format(self.__transaction_id) + "/latest")
                return payjunctionrestlib.Receipts(receipts['uri'], receipts['signatureStatus'], receipts['terms'], receipts['signatureUpToDate'], receipts['signature'],
                                                    receipts['documents'], receipts['actions'], receipts['created'], receipts['lastModified'])
            else:
                raise TypeError("The payjunctionrestlib object is not longer available")
                
        def get_fullpage_receipt(self):
            if self.__hook is not None:
                return self.__hook.get(payjunctionrestlib.TRANSACTIONS + payjunctionrestlib.RECEIPTS
            
    class Note(object):
        
        __note_id = None
        __uri = None
        __text = ""
        __created = None
        __last_mod = None
        __user = None
        
        def __init__(self, n_id, uri, text, created, lm, user):
            self.__note_id = n_id
            self.__uri = uri
            self.__text = text
            self.__created = created
            self.__last_mod = lm
            self.__user = user
        
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
        
        def text(self):
            return self.__text
        
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
        
        __hook = None
        __customer_id = None
        __uri = None
        __first_name = None
        __last_name = None
        __company_name = None
        __email = None
        __phone = None
        __phone2 = None
        __job_title = None
        __identifier = None
        __website = None
        __custom1 = None
        __created = None
        __last_mod = None
        __addresses = None
        __default_address = None
        __vaults = None
        
        def __init__(self, hook, c_id, uri, first, last, company, email, phone, phone2, job, ident, web, custom, created, lm, addresses, default, vaults):
            self.__hook = hook
            self.__customer_id = c_id
            self.__uri = uri
            self.__first_name = first
            self.__last_name = last
            self.__company_name = company
            self.__email = email
            self.__phone = phone
            self.__phone2 = phone2
            self.__job_title = job
            self.__identifier = ident
            self.__website = web
            self.__custom1 = custom
            self.__created = created
            self.__last_mod = lm
            self.__addresses = addresses
            self.__default_address = default
            self.__vaults = vaults
        
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