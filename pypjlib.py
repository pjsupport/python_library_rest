class payjunctionrestlib:
    """ A library containing classes for processing requests on the PayJunction REST API
    """
    
    import requests
    import json
    from exceptions import ValueError, KeyError
    
    #Constants for API endpoints
    TRANSACTIONS = "/transactions/"
    CUSTOMERS = "/customers/"
    
    __login = ""
    __password = ""
    __app_key = ""
    __test = False
    
    def __init__(self, login, passwd, key, test=False):
        self.__login = login
        self.__password = passwd
        self.__app_key = key
        self.__test = test
        
    def verify(self, to_test, required):
        for key in required:
            if key not in to_test:
                raise KeyError(key + " is a required parameter for this transaction type.")
            if not to_test[key]:
                raise ValueError(key + " cannot be empty or None.")
            
    def post(self, ptype, data):
        
        headers = {"PJ-X-Application-Key" : self.__app_key}
        auth = requests.auth.HTTPBasicAuth(self.__login, self.__password)
        
        url = ""
        if (self.__test == False):
            url = "https://api.payjunction.com"
        else:
            url = "https://api.payjunctionlabs.com"
        
        url += ptype
        
        r = requests.post(url=url, data=data, auth=auth)
        
        if (r.status_code == requests.codes.ok):
            json_response = r.json()
            raw_response = r.text
            r = None # Make sure GC clears the memory with the card and authentication info in it as soon as possible
            return (json_response, raw_response)
        else:
            r.request = None # Make sure GC clears the memory with the card and authentication info in it as soon as possible
            r.raise_for_status()
        
        
    class Transaction(object):
        
        #Constants for use with create()
        KEYED = 1
        SWIPED = 2
        ACH = 3
        
        __notes = []
        __receipts = None
        __transaction_id = 0
        __uri = ""
        __terminal_id = 0
        __action = ""
        __amount_base = 0.00
        __amount_tax = 0.00
        __amount_shipping = 0.00
        __amount_tip = 0.00
        __amount_surcharge = 0.00
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
        __vault = {
            "type" : "",
            "acocuntType": "",
            "lastFour": ""
            }

        __billing = {
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
        }
        __shipping = {
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
        }
        __json = ""
        
        def __init__(self, notes, receipts, txnid, uri, terid, action, ab, total, 
        inv, po, status, created, lm, response, settlement, vault, billing, 
        shipping, js, at=0.00, ash=0.00, atip=0.00, asur=0.00):
            self.__notes = notes
            self.__receipts = receipts
            self.__transaction_id = txnid
            self.__uri = uri
            self.__terminal_id = terid
            self.__action = action
            self.__amount_base = ab
            self.__amount_tax = at
            self.__amount_shipping = ash
            self.__amount_tip = at
            self.__amount_surcharge = asur
            self.__amount_total = total
            self.__invoice_number = inv
            self.__purchase_order_number = po
            self.__status = status
            self.__created = created
            self.__last_mod = lm
            self.__response = response
            self.__settlement = settlement
            self.__vault = vault
            self.__billing = billing
            self.__shipping = shipping
            self.__json = js
        
        def create(self, type_constant, params):
            #Verify we have the required parameters for the transaction type
            if (type_constant == self.KEYED):
                #Verify we have all required fields for a keyed transaction
                payjunctionrestlib.verify(params, ("cardNumber", "cardExpMonth", "cardExpYear", "amountBase"))
                    
            elif type_constant == self.SWIPED:
                payjunctionrestlib.verify(params, ("cardSwipe", "amountBase"))
                        
            elif type_constant == self.ACH:
                payjunctionrestlib.verify(params, ("achRoutingNumber", "achAccountNumber", "achAccountType", "achType", "amountBase"))
            
            else:
                raise ValueError(type_constant + " is not valid for type_constant")
            
            
             
        def get(self, t_id):
            #TODO
            pass
        
        def update(self):
            #TODO
            pass
        
        def recharge(self, amount=None):
            #TODO
            pass
            
        def void(self):
            #TODO
            pass
            
        def refund(self):
            #TODO
            pass
    
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