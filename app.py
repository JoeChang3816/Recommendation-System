#When its finished, enable anything thats related to stopwords, and remove (inputtedSearchText = urlSearchBar)

from __future__ import division
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, current_user, LoginManager
from os import path
from sqlalchemy import or_, and_
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
import re

from decimal import *

app = Flask(__name__)

#############################
app.config['SECRET_KEY'] = 'FDHGFDHGH FHRTGHDFHRTHRH'

#localhost
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/fyp'

db = SQLAlchemy(app) #use SQLAlchemy to connect mySQL
from dbmodel import Users, Products, PurchaseHistory, CustomerProfile #import classes/tables, so must be placed before db.create_all()

with app.app_context():

    #Enable these two codes if you just install the store to your pc.
    #db.create_all() #is used to create a new table into the database, This method will first check whether the table exists in the database or not if suppose it has found an existing table it will not create any table
    #db.init_app(app)

    if(Users.query.filter_by(userName="DU").first() is None):
        newUser = Users(userName = "DU")
        db.session.add(newUser)
        db.session.commit() #Confirm and update
    
    ##############################
login_manager = LoginManager()
login_manager.login_view = 'app.userProfilePage_User'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userID):
    return Users.query.get(userID)

#Routes
#Homepage
@app.route("/", methods=['POST', 'GET'])
def home():
    defaultLogin()
    UpdateCustomerProfile()

    from RS import RecommendProduct_CollaborativeFiltering, RecommendedProducts_ContentBased, FindSimilarUser_CF

    #1st para: recommedation choice based on user's profile higest weights on Type and subtype
    #2nd para: recommedation based on weights sum calcautions
    RProducts_ContentBased = RecommendedProducts_ContentBased(5, 5) #5 + 5 = 10 products in total to be recommended

    #################################

    #1st para: maxiumum number of products to be recommended
    #2nd para: lowest rating of product that was purchased by similar users
    RProducts_CollaborativeFiltering = RecommendProduct_CollaborativeFiltering(10, 4)

    if(request.method == 'POST'):
        if(request.form['userSubmitButton'] == "search"):
            return performSearching()

    return render_template('Home.html', user = current_user, RP_ContentBased = RProducts_ContentBased, RP_advanced = RProducts_CollaborativeFiltering) #If user click home button, this one will be active instead

@app.route("/search", methods=['GET','POST'])
def search():

    defaultLogin()

    if(request.method == 'POST'):
        if(request.form['userSubmitButton'] == "search"):
            return performSearching()
    

    #There is where searching begins
    else:

        urlSearchBar = request.args.get('searchBar') #Search Query
        urlsearchType = request.args.get('searchType') #Requested Type
        urlsearchSubType = request.args.get('searchSubType') #Requested Sub-Type

        urlSearchBar = removeStopWords(urlSearchBar) 

        urlSearchBarToken = urlSearchBar.split() #Iron Man -> [Iron,Man]
        urlsearchType = urlsearchType.split() #3DPrint Game -> [3DPrint, Game]
        urlsearchSubType = urlsearchSubType.split() #Character Weapon -> [Character, Weapon]

        print("===============================")
        print("Query: ", urlSearchBar)
        print("\nType Selected: ", urlsearchType)
        print("\nSubtype Selected: ", urlsearchSubType)

        dbQueryResult = []

        #If search bar is not empty
        if(len(urlSearchBarToken) != 0):
            
            filter_list = [Products.productName.contains(x) for x in urlSearchBarToken]
            dbQueryResult = Products.query.filter(or_(*filter_list)).all()

            # # #For debug purpose
            # print("O Search Result")
            # for x in dbQueryResult:
            #      print(x.productName)
            
            #Get all products that contains the words Iron & Man
            #not "Ir" "on" "ro" etc
            ProductsListTemp = []
            for x in urlSearchBarToken:
                for y in dbQueryResult:
                    if(findWholeWord(x)(y.productName) is not None and y not in ProductsListTemp):
                        ProductsListTemp.append(y)

            dbQueryResult = ProductsListTemp #A new dbQueryResult

            ProductsListTemp = []

            #Logical expression:
            #Type or Type
            #Subtype or Subtype
            #Type and (Subtype or Subtype)

            for x in dbQueryResult:
                
                if(len(urlsearchType) != 0 and len(urlsearchSubType) != 0): #both selected

                    #Start from bottom
                    #Only one sub-type in product
                    if(" " not in x.productSubType):
                        if(x.productSubType in urlsearchSubType and x not in ProductsListTemp):
                            ProductsListTemp.append(x)
                    
                    #More than one sub-type
                    elif(" " in x.productSubType):
                        for y in urlsearchSubType:
                            if(y in x.productSubType and x not in ProductsListTemp):
                                ProductsListTemp.append(x)
                                break

                    if(ProductsListTemp != []):
                        for y in ProductsListTemp:
                            if (y.productType not in urlsearchType):
                                ProductsListTemp.remove(y)
                        
                elif(len(urlsearchType) != 0 and len(urlsearchSubType) == 0): #Only urlsearchType selected
                    
                    if(x.productType in urlsearchType and x not in ProductsListTemp):
                        ProductsListTemp.append(x)

                elif(len(urlsearchSubType) != 0 and len(urlsearchType) == 0): #Only urlsearchSubType selected

                    #Only one sub-type in product
                    if(" " not in x.productSubType):
                        if(x.productSubType in urlsearchSubType and x not in ProductsListTemp):
                            ProductsListTemp.append(x)
                    
                    #More than one sub-type
                    elif(" " in x.productSubType):
                        for y in urlsearchSubType:
                            if(y in x.productSubType and x not in ProductsListTemp):
                                ProductsListTemp.append(x)
                                break
                    
                if(len(urlsearchType) == 0 and len(urlsearchSubType) == 0): 
                    pass
                else:
                    dbQueryResult = ProductsListTemp
        
        #If search bar is empty, but filter list is filled, than return result based on selected type and subtype
        elif(len(urlsearchType) != 0 or len(urlsearchSubType) != 0):
            dbQueryResult = getProductListByTypeORSubType(urlsearchType, urlsearchSubType)

        ###### Original Basic Search System ######
        #In ranking, prioritize products whose full name contains "Iron Man"
        #Search: Iron Man  ;
        #           Iron Man = 2;
        #           Iron = 1;
        #           Iron Man Suit = 2;
        #Iron:
        #Iron Man = 1/2
        #Iron = 1/1
        #Iron Man Suit = 1/3
        weightForProduct = []

        for x in dbQueryResult:

            currentWeight = 0.00

            for y in urlSearchBarToken:
                if(y in x.productName):
                    currentWeight = currentWeight + 1.00

            weightForProduct.append(currentWeight)
        
        print("weightForProduct: ", weightForProduct)

        #[1, 3, 2, 6]
        #[one, three, two, six] = list of products
        #to
        #[6, 3, 2, 1]
        #[six, three, two, one]
        #Highest weight = 1st in ranking
        dbQueryResult = sortByReference(dbQueryResult, weightForProduct)
        #############################################
                                
        from PSS import PersonlizedSearchingResult
        dbQueryResult = PersonlizedSearchingResult(urlSearchBarToken, dbQueryResult)

    return render_template("Search.html", user = current_user, productSearchResults = dbQueryResult)


@app.route("/user-user", methods=['POST', 'GET'])
def userProfilePage_User():

    from RS import createCustomerProfile
    defaultLogin()
    UpdateCustomerProfile()
    
    if(request.method == 'POST'):

        if(request.form['userSubmitButton'] == "search"):
            return performSearching()

        #Add User
        elif(request.form['userSubmitButton'] == "addUserButton"):
            inputtedNewUsername = request.form.get('newusername')
            inputtedNewAge = request.form.get('newage')
            inputtedNewGender = request.form.get('newgender')

            inputtedNewUserInterestTypeArray = request.form.getlist('InterestModelType')
            inputtedNewUserInterestSubTypeArray = request.form.getlist('InterestModelSubType')

            #Array to String: [1,2,3] > 1 2 3
           
            inputtedNewUserInterestType = " ".join([str(elem) for elem in inputtedNewUserInterestTypeArray])
            inputtedNewUserInterestSubType = " ".join([str(elem) for elem in inputtedNewUserInterestSubTypeArray])

            queryUser = Users.query.filter_by(userName=inputtedNewUsername).first()
            
            if(queryUser is not None and queryUser.userName == inputtedNewUsername): #If username already existed in database
                flash("User " + inputtedNewUsername+ " is already existed !", category="error")

            elif(len(inputtedNewUsername) > 0):
                #Add new user to database
                newUser = Users(userName = inputtedNewUsername, 
                                gender = inputtedNewGender, 
                                age = inputtedNewAge, 
                                interestType = inputtedNewUserInterestType, 
                                interestSubType = inputtedNewUserInterestSubType, 
                                totalPurchasedModels = 0)
                
                db.session.add(newUser)
                db.session.commit() #Confirm and update

                createCustomerProfile()
                
                flash("User " + inputtedNewUsername+ " added !", category="success")

        #Switch User
        elif(request.form['userSubmitButton'] == "switchUserButton"):

            inputtedSwitchUsername = request.form.get('switchUsername')
            queryUser = Users.query.filter_by(userName=inputtedSwitchUsername).first()

            if(queryUser is not None and queryUser.userName == inputtedSwitchUsername): ##If username already existed in database
                flash("Now changed to " + inputtedSwitchUsername + " !", category="success")
                login_user(queryUser, remember=True)

            else:
                flash("User " + inputtedSwitchUsername+ " does not existed!", category="error")

         #Change Interest
        elif(request.form['userSubmitButton'] == "changeUserInterestButton"):

            inputtedTargetedUsername = request.form.get('usernameChangeInterest')
            inputtedChangedUserInterestTypeArray = request.form.getlist('changeInterestModelType')
            inputtedChangedUserInterestSubTypeArray = request.form.getlist('changeInterestModelSubType')

            #Array to String: [1,2,3] > 1 2 3
           
            inputtedChangedUserInterestType = " ".join([str(elem) for elem in inputtedChangedUserInterestTypeArray])
            inputtedChangedUserInterestSubType = " ".join([str(elem) for elem in inputtedChangedUserInterestSubTypeArray])
            
            
            queryUser = Users.query.filter_by(userName=inputtedTargetedUsername).first()

            if(queryUser is not None): #If username already existed in database
                queryUser.interestType = inputtedChangedUserInterestType
                queryUser.interestSubType = inputtedChangedUserInterestSubType
                db.session.commit()
                UpdateCustomerProfile()

                flash("User " + queryUser.userName + " 's interest changed !", category="success")
            else:
                flash("User " + inputtedTargetedUsername+ " does not existed!", category="error")

    return render_template("user_user.html", user = current_user, 
                            interestedTypes = Str2Array(current_user.interestType), 
                            interestedSubTypes = Str2Array(current_user.interestSubType),
                            CP = CustomerProfile.query.filter_by(userID = current_user.id).first())

@app.route("/user-product", methods=['POST', 'GET'])
def userProfilePage_Product():

    defaultLogin()

    if(request.method == 'POST'):


        if(request.form['userSubmitButton'] == "search"):
            return performSearching()

        #Add Product
        elif(request.form['userSubmitButton'] == "addProductButton"):
            inputtedProductName = request.form.get('productName')
            inputtedProductType = request.form.get('ModelType')
            inputtedProductSubTypeArray = request.form.getlist('ModelSubType')
            inputtedPrice = request.form.get('productPrice')

            if(inputtedPrice is not None and inputtedProductName is not None and inputtedProductType is not None):

                #Array to String: [1,2,3] > 1 2 3
                inputtedProductSubType = " ".join([str(elem) for elem in inputtedProductSubTypeArray])
                
                newProduct = Products(productName = inputtedProductName, 
                                    productType = inputtedProductType, 
                                    productSubType = inputtedProductSubType, 
                                    productPrice = inputtedPrice,
                                    uploaderID = current_user.id,
                                    totalSales = 0)

                db.session.add(newProduct)
                db.session.commit() #Confirm and update
                flash("New product added !", category="success")
            else:

                flash("Price/Name/Type cannot be empty", category="error")

        #Modify Product Details
        elif(request.form['userSubmitButton'] == "changedProductButton"):

            inputtedTargetedProductID = int(request.form.get('changedProductID'))
            inputtedTargetedProductName = request.form.get('changedProductName')

            inputtedChangedProductType = request.form.get('changedModelType')
            inputtedChangedProductSubTypeArray = request.form.getlist('changedModelSubType')
            inputtedChangedProductSubType = " ".join([str(elem) for elem in inputtedChangedProductSubTypeArray])
           
            inputtedChangedProductPrice = Decimal(request.form.get('changedProductPrice'))

            queryProduct = Products.query.filter_by(productID=inputtedTargetedProductID).first()

            if(queryProduct is not None): #If the product exists

                queryProduct.productName = inputtedTargetedProductName
                queryProduct.productType = inputtedChangedProductType
                queryProduct.productSubType = inputtedChangedProductSubType
                queryProduct.productPrice = inputtedChangedProductPrice

                db.session.commit()
                
                flash("Product's detail changed !", category="success")
            else:
                flash("Product does not existed!", category="error")

    return render_template("user_product.html", user = current_user)

@app.route("/user-purchase", methods=['POST', 'GET'])
def userProfilePage_Purchase():
    
    from RS import createCustomerProfile
    defaultLogin()

    queryAllpurchasedProductHistories = PurchaseHistory.query.filter_by(userID = current_user.id).all()
    localProductDetails = []

    for data in queryAllpurchasedProductHistories:

        current_productID = data.productID
        localProductDetails.append(Products.query.filter_by(productID = current_productID).first())
    

    if(request.method == 'POST'):

        if(request.form['userSubmitButton'] == "search"):
            return performSearching()

        #Buy Model 
        elif(request.form['userSubmitButton'] == "buyProductButton"):

            inputtedProductID = int(request.form.get('purchasedProductID')) #ID is int in database
            queryHistory = PurchaseHistory.query.filter_by(userID=current_user.id).all()
            targetedProduct = Products.query.filter_by(productID=inputtedProductID).first()
            targetedUser = Users.query.filter_by(id=current_user.id).first()

            buyBool = False
            if(targetedProduct is not None): #Check existence of model
                buyBool = True
                if(queryHistory is not None): #Check user's purchase history
                    for x in queryHistory:
                        #To avoid user buy the model twice
                        if(x.productID == inputtedProductID):
                            flash("You have already bought the model!", category="error")
                            buyBool = False
                            break
            else:
                flash("Model does not exist!", category="error")
             
            if(buyBool == True):
                newPurchaseHistory = PurchaseHistory(userID = current_user.id, 
                                                    productID = inputtedProductID,
                                                    productRating = 0)
               
                db.session.add(newPurchaseHistory)
                if(targetedProduct.totalSales is not None):
                    targetedProduct.totalSales = targetedProduct.totalSales + 1
                else:
                    targetedProduct.totalSales = 1

                targetedUser.totalPurchasedModels = targetedUser.totalPurchasedModels + 1

                db.session.commit() #Confirm and update

                #To update profile after purchased new stuff
                createCustomerProfile()

                flash("Model Purchased !", category="success")

        #Rate Model 
        elif(request.form['userSubmitButton'] == "rateProductButton"):

            inputtedProductID = int(request.form.get('ratedProductID')) #id is int in database
            inputtedProductRating = int(request.form.get('ratingInput')) #id is int in database

            queryHistory = PurchaseHistory.query.filter(and_(PurchaseHistory.productID == inputtedProductID), (PurchaseHistory.userID == current_user.id)).first()

            if(queryHistory is not None):

                queryHistory.productRating = inputtedProductRating
                db.session.commit()
                flash("Model rated !", category="success")

                createCustomerProfile()

            elif(Products.query.filter_by(productID=inputtedProductID).first() is None):
                flash("Model does not exist !", category="error")
                
            else:
                flash("You have not bought the model yet!", category="error")
       
    return render_template("user_purchase.html", user = current_user, purchasedProducts = queryAllpurchasedProductHistories, productDetails = localProductDetails)




'''
#ProductList
#/type/sub-type/productname
@app.route("/<productname>")
def product(productname):
    return "<p>Hello {productname}</p>"
'''
if __name__ == "__main__":
    app.run(debug=True)


def Str2Array(x):
    if(x is not None):
        x = x.split() # '1 2 3' -> ['1', '2', '3']
        return x

def removeStopWords(x):

    xArray = x.split()
    resultwords  = [word for word in xArray if word.lower() not in stopwords.words('english')]
    result = ' '.join(resultwords)
    return result

#Its because the search bar is in every page.... So, it has to be a function

def findWholeWord(x):
    return re.compile(r'\b({0})\b'.format(x), flags=re.IGNORECASE).search

#This function is used for gathering queries from url and then redirect website to search.html
def performSearching():

    inputtedSearchBar = request.form.get('SearchQueryBar') 
    inputtedSearchTypeQueryArray = request.form.getlist('SearchModelType') #problem: site cannot detect
    inputtedSearchSubTypeQueryArray = request.form.getlist('SearchModelSubType')

    inputtedSearchTypeQuery = " ".join([str(elem) for elem in inputtedSearchTypeQueryArray])
    inputtedSearchSubTypeQuery = " ".join([str(elem) for elem in inputtedSearchSubTypeQueryArray])

    return redirect(url_for("search", searchBar=inputtedSearchBar, searchType=inputtedSearchTypeQuery, searchSubType=inputtedSearchSubTypeQuery))

def sortByReference(lst, Ref):

    index = list(range(len(Ref)))
    index.sort(key = Ref.__getitem__)

    lst[::-1] = [lst[i] for i in index]

    return lst

def defaultLogin():
    if (not current_user.is_authenticated):
        queryUser = Users.query.filter_by(userName= "DU").first()
        login_user(queryUser)


def UpdateCustomerProfile():
    from RS import createCustomerProfile

    targetUser = Users.query.filter_by(id = current_user.id).first()
    getCustomerProfile = CustomerProfile.query.filter_by(userID = current_user.id).first()

    #To recreate missing profile
    if(getCustomerProfile is None and targetUser.totalPurchasedModels != 0):
        createCustomerProfile()

    #To update profile after changed interested (For users who haven't bought anything yet)
    elif(targetUser.totalPurchasedModels == 0):
        createCustomerProfile()

        
def getProductListByTypeORSubType(selectedType, selectedSubType):

    ProductsListType = []
    ProductsListSubType = []

    if(len(selectedType) != 0):
        filter_list = [Products.productType.contains(x) for x in selectedType]
        ProductsListType = Products.query.filter(or_(*filter_list)).all()

    if(len(selectedSubType) != 0):
        filter_list = [Products.productSubType.contains(x) for x in selectedSubType]
        ProductsListSubType = Products.query.filter(or_(*filter_list)).all()

    ProductsList = ProductsListType + ProductsListSubType #Combine two list together, but somehow it can remove duplicated elements.

    return ProductsList

def getProductListByTypeANDSubType(selectedType, selectedSubType):
    
    filter_list1 = [Products.productType.contains(x) for x in selectedType]
    filter_list2 = [Products.productSubType.contains(x) for x in selectedSubType]

    return Products.query.filter( and_ (*filter_list1, *filter_list2) ).all()


