from app import db, sortByReference
from dbmodel import Users, Products, PurchaseHistory, CustomerProfile
from flask_login import current_user
import numpy as np 

############### Personlized Searching ###############

#Return search result which is a list of products

#There are three section for search result: | All fulfilled | Query fulfilled | Partially fulfilled |
    #Eg: Search:    Iron Man
    #Product Name:  Iron Man Helmet = Query fufilled
    #               Iron Ingot      = Partially fufilled
    #               Iron Man        = All fufilled

    #Typically, "All fufilled" will only satisfy one products, so no personlization needed.

#Products inside each section will be reranked their order.

def PersonlizedSearchingResult(SearchQueryToken, OrginialSearchProductResults):
    
    print("\nSearch Query Token: ", SearchQueryToken)
    print("Original Search Results:", OrginialSearchProductResults)

    #To break down OrginialSearchProductResults into two section: All fulfilled + Query fulfilled + Partially fulfilled
    i = 0
    NestBreak = False
    AllFulfilledResult = 0
    for OProducts in OrginialSearchProductResults:

        for x in range(len(SearchQueryToken)):
            if(SearchQueryToken[x] not in OProducts.productName): 
                NestBreak = True
                break
            
            elif(x == (len(SearchQueryToken)-1) and len(SearchQueryToken) == len(OProducts.productName.split()) ):
                AllFulfilledResult = OProducts

        if(NestBreak == True):
            break
        else:
            i=i+1
    
    QueryFulfilledResult = OrginialSearchProductResults[:i]
    PartiallyFulfilledResult = OrginialSearchProductResults[i:]

    if(AllFulfilledResult != 0):
        QueryFulfilledResult.remove(AllFulfilledResult)

    print("\nAll fulfilled section: ", AllFulfilledResult)
    print("Query fulfilled section: ", QueryFulfilledResult)
    print("Partially fulfilled section: ", PartiallyFulfilledResult)
    print("\n===============================")

    ####
    #Personlization:
    QueryFWeights = SearchedProductWeightList(QueryFulfilledResult)
    PartWeights = SearchedProductWeightList(PartiallyFulfilledResult)

    print("QWeight", QueryFWeights)
    print("PWeight", PartWeights)

    #For better dsplaying result in store:
    sortedQueryF = sortByReference(QueryFulfilledResult, QueryFWeights)
    sortedPart = sortByReference(PartiallyFulfilledResult, PartWeights)

    if(len(sortedQueryF) > 1):
        sortedQueryF = np.append(sortedQueryF, 'hr')

        if(AllFulfilledResult != 0 ):
            sortedQueryF = np.insert(sortedQueryF, 0, 'hr')

    if(len(sortedQueryF) == 0 and AllFulfilledResult != 0 and len(sortedQueryF) != 0):
            sortedPart = np.insert(sortedPart, 0, 'hr')

    #Add lists together
    FinalList = np.concatenate((sortedQueryF, sortedPart), axis=0)

    #Add AllFulfilledResult to FinalLists
    if(AllFulfilledResult != 0 and len(FinalList) != 0 ):
        FinalList = np.insert(FinalList, 0, AllFulfilledResult)
    elif(AllFulfilledResult != 0 and len(FinalList) == 0):
        FinalList = np.array([AllFulfilledResult])

    ####

    print("Full Results: ", FinalList)
    
    return FinalList

def SearchedProductWeightList(ProductList):
     
    getCustomerProfile = CustomerProfile.query.filter_by(userID = current_user.id).first()
    weightForProduct = np.array([])

    #Give weight to each result
    for x in ProductList:

        if("3DPrint" in x.productType):
                weight = getCustomerProfile.Print
        elif("Game" in x.productType):
                weight = getCustomerProfile.Game
        elif("PBR" in x.productType):
                weight = getCustomerProfile.PBR
        elif("" in x.productType):
                weight = 0

        if("Animal" in x.productSubType):
                weight += getCustomerProfile.Animal

        if("Character" in x.productSubType):
                weight += getCustomerProfile.Character

        if("Food" in x.productSubType):
                weight += getCustomerProfile.Food

        if("Plant" in x.productSubType):
                weight += getCustomerProfile.Plant

        if("Weapon" in x.productSubType):
                weight += getCustomerProfile.Weapon

        if("Vehicle" in x.productSubType):
                weight += getCustomerProfile.Vehicle
                
        if("" in x.productSubType):
                weight += 0

        weightForProduct = np.append(weightForProduct, weight)

    return weightForProduct
