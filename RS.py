from app import db, getProductListByTypeORSubType
from dbmodel import Users, Products, PurchaseHistory, CustomerProfile
from flask_login import current_user
import numpy as np 
import pandas as pd
from sqlalchemy import and_
import random
from sklearn import preprocessing
from sklearn.neighbors import NearestNeighbors

#Create customer profile (Merge Type and Sub-Type Version)
"""def createProfile():

    productHistories = PurchaseHistory.query.filter_by(userID = current_user.id).all()

    RateMatrix = pd.DataFrame()

    for data in productHistories:
        
        rating = data.productRating

        #Ignore those did not rated/ Do not take unrated products into consideration
        if(rating is not None):
            CurrentProductDetail = Products.query.filter_by(productID = data.productID).first()

            localSubType = CurrentProductDetail.productSubType
            #Example: 3DPrint-Animal, Game-Weapon, 3DPrint-Character-Weapon
            TypeColumn = CurrentProductDetail.productType + '-' + localSubType
            #3DPrint-Character Weapon -> 3DPrint-Character-Weapon
            TypeColumn = TypeColumn.replace(" ", "-")

            #Avoid duplicate column
            if TypeColumn not in RateMatrix.columns:
                RateMatrix.insert(0, TypeColumn, 0, True)

            RateMatrix = pd.concat([RateMatrix, pd.DataFrame(index=[data.productID])])

            RateMatrix.loc[data.productID, TypeColumn] = rating

    #Replace every NaN in dataset to  0
    #RateMatrix = RateMatrix.fillna(0)

    #Replace every 0 in dataset to NaN, we do that because we want to calcaute the "means", otherwise it would also take 0 to mean calculation
    RateMatrixNon = RateMatrix.replace(0, np.NaN)
    
    #RateMatrix.sum() = Sum all the rate together group by the type
    NormalizedMean = preprocessing.normalize([RateMatrixNon.mean()])

    CustomerProfile = pd.DataFrame(NormalizedMean, columns=RateMatrix.columns, index=["RatedWeight"])
    CustomerProfile = CustomerProfile.swapaxes("index", "columns")

    #Sort weights
    CustomerProfile = CustomerProfile.sort_values(by=['RatedWeight'], ascending = False)

    return CustomerProfile
"""

def createCustomerProfile():

    getCustomerProfile = CustomerProfile.query.filter_by(userID = current_user.id).first()
    productHistories = PurchaseHistory.query.filter_by(userID = current_user.id).all()
    currentUserFilter = Users.query.filter_by(id = current_user.id).first()

    RateMatrix = pd.DataFrame(columns=['3DPrint', 'Game', 'PBR', 
                                       'Animal', 'Character', 'Food', 'Plant', 'Weapon', 'Vehicle'])

    #Have purchased something
    if(len(productHistories) != 0):

        for data in productHistories:
            
            rating = data.productRating

            #Ignore products that did not rated and do not take unrated products into consideration
            if(rating is not None and rating != 0):
                newRow= [0,0,0,0,0,0,0,0,0]

                CurrentProductDetail = Products.query.filter_by(productID = data.productID).first()
            
                if("3DPrint" in CurrentProductDetail.productType):
                    newRow[0] = rating
                elif("Game" in CurrentProductDetail.productType):
                    newRow[1] = rating
                elif("PBR" in CurrentProductDetail.productType):
                    newRow[2] = rating

                if("Animal" in CurrentProductDetail.productSubType):
                    newRow[3] = rating
                if("Character" in CurrentProductDetail.productSubType):
                    newRow[4] = rating
                if("Food" in CurrentProductDetail.productSubType):
                    newRow[5] = rating
                if("Plant" in CurrentProductDetail.productSubType):
                    newRow[6] = rating
                if("Weapon" in CurrentProductDetail.productSubType):
                    newRow[7] = rating
                if("Vehicle" in CurrentProductDetail.productSubType):
                    newRow[8] = rating
                    
                RateMatrix.loc[data.productID] = newRow

        #RateMatrix.sum() = Sum all the rate together group by the type
        RateMatrixSum = np.split(RateMatrix.sum(), [3], axis=0)

        print("RateMatrix :", RateMatrix)
        print("RateMatrixSum :", RateMatrix.sum())

        RateMatrixTypeSum = RateMatrixSum[0]
        RateMatrixSubTypeSum = RateMatrixSum[1]

        Normalized_Type = preprocessing.normalize([RateMatrixTypeSum])
        Normalized_SubType = preprocessing.normalize([RateMatrixSubTypeSum])

        print("Normalized_Type: ",Normalized_Type)

        #Merging two table back together
        df1 = pd.DataFrame(Normalized_Type, columns=['3DPrint', 'Game', 'PBR'], index=["RatedWeight"])
        df2 = pd.DataFrame(Normalized_SubType, columns=['Animal', 'Character', 'Food', 'Plant', 'Weapon', 'Vehicle'], index=["RatedWeight"])
        
        df1 = df1.swapaxes("index", "columns")
        df2 = df2.swapaxes("index", "columns")

        CP = pd.concat([df1, df2], axis=0, join='inner')
        
        print("\n Customer Profile: \n", CP)

        if(getCustomerProfile is not None):
            getCustomerProfile.Print = CP.loc["3DPrint"]["RatedWeight"]
            getCustomerProfile.Game = CP.loc["Game"]["RatedWeight"]
            getCustomerProfile.PBR = CP.loc["PBR"]["RatedWeight"]
            getCustomerProfile.Animal = CP.loc["Animal"]["RatedWeight"]
            getCustomerProfile.Character = CP.loc["Character"]["RatedWeight"]
            getCustomerProfile.Food = CP.loc["Food"]["RatedWeight"]
            getCustomerProfile.Plant = CP.loc["Plant"]["RatedWeight"]
            getCustomerProfile.Weapon = CP.loc["Weapon"]["RatedWeight"]
            getCustomerProfile.Vehicle = CP.loc["Vehicle"]["RatedWeight"]
            getCustomerProfile.TotalAnalysedProducts = RateMatrix.shape[0]

            db.session.commit()
        
        else:
            
            newCustomerProfile = CustomerProfile(
                userID = current_user.id,
                Print = CP.loc["3DPrint"]["RatedWeight"],
                Game = CP.loc["Game"]["RatedWeight"],
                PBR = CP.loc["PBR"]["RatedWeight"],
                Animal = CP.loc["Animal"]["RatedWeight"],
                Character = CP.loc["Character"]["RatedWeight"],
                Food = CP.loc["Food"]["RatedWeight"],
                Plant = CP.loc["Plant"]["RatedWeight"],
                Weapon = CP.loc["Weapon"]["RatedWeight"],
                Vehicle = CP.loc["Vehicle"]["RatedWeight"],
                TotalAnalysedProducts = RateMatrix.shape[0])
            
            db.session.add(newCustomerProfile)
            db.session.commit() #Confirm and update
    
    #Have not purchased anything yet,
    elif(len(productHistories) == 0):
        
        #but provided interested product types
        if(currentUserFilter.interestType !="" or currentUserFilter.interestSubType !=""):

            localInterestedType = currentUserFilter.interestType.split()
            localInterestedSubType = currentUserFilter.interestSubType.split()

            if(getCustomerProfile is not None):
                
                if("3DPrint" in localInterestedType):
                    getCustomerProfile.Print = 1
                else:
                    getCustomerProfile.Print = 0

                if("Game" in localInterestedType):
                    getCustomerProfile.Game = 1
                else:
                    getCustomerProfile.Game = 0

                if("PBR" in localInterestedType):
                    getCustomerProfile.PBR = 1
                else:
                    getCustomerProfile.PBR = 0
                
                ####################################

                if("Animal" in localInterestedSubType):
                    getCustomerProfile.Animal = 1
                else:
                    getCustomerProfile.Animal = 0
                
                if("Character" in localInterestedSubType):
                    getCustomerProfile.Character = 1
                else:
                    getCustomerProfile.Character = 0

                if("Food" in localInterestedSubType):
                    getCustomerProfile.Food = 1
                else:
                    getCustomerProfile.Food = 0

                if("Plant" in localInterestedSubType):
                    getCustomerProfile.Plant = 1
                else:
                    getCustomerProfile.Plant = 0

                if("Weapon" in localInterestedSubType):
                    getCustomerProfile.Weapon = 1
                else:
                    getCustomerProfile.Weapon = 0

                if("Vehicle" in localInterestedSubType):
                    getCustomerProfile.Vehicle = 1
                else:
                    getCustomerProfile.Vehicle = 0
                
                ####################################

                getCustomerProfile.TotalAnalysedProducts = 0

                db.session.commit()

            #Just in case the profile is accidentally deleted.
            elif(getCustomerProfile is None):
                
                newCustomerProfile = CustomerProfile(userID = current_user.id, Print = 0, Game = 0, PBR = 0, Animal = 0, Character = 0, Food = 0, Plant = 0, Weapon = 0, Vehicle = 0, TotalAnalysedProducts = 0)
                    
                db.session.add(newCustomerProfile)
                db.session.commit()

                getCustomerProfile = CustomerProfile.query.filter_by(userID = current_user.id).first()

                if("3DPrint" in localInterestedType):
                    getCustomerProfile.Print = 1
                else:
                    getCustomerProfile.Print = 0

                if("Game" in localInterestedType):
                    getCustomerProfile.Game = 1
                else:
                    getCustomerProfile.Game = 0

                if("PBR" in localInterestedType):
                    getCustomerProfile.PBR = 1
                else:
                    getCustomerProfile.PBR = 0
                
                ####################################

                if("Animal" in localInterestedType):
                    getCustomerProfile.Animal = 1
                else:
                    getCustomerProfile.Animal = 0
                
                if("Character" in localInterestedType):
                    getCustomerProfile.Character = 1
                else:
                    getCustomerProfile.Character = 0

                if("Food" in localInterestedType):
                    getCustomerProfile.Food = 1
                else:
                    getCustomerProfile.Food = 0

                if("Plant" in localInterestedType):
                    getCustomerProfile.Plant = 1
                else:
                    getCustomerProfile.Plant = 0

                if("Weapon" in localInterestedType):
                    getCustomerProfile.Weapon = 1
                else:
                    getCustomerProfile.Weapon = 0

                if("Vehicle" in localInterestedType):
                    getCustomerProfile.Vehicle = 1
                else:
                    getCustomerProfile.Vehicle = 0
                
                ####################################

                getCustomerProfile.TotalAnalysedProducts = 0

                db.session.commit()

        #or, didn't actively provide anything
        else:
            
            #All need to set to 0 just in case if someone deliberately decided to remove all interested type
            if(getCustomerProfile is not None):
                
                getCustomerProfile.Print = 0
                getCustomerProfile.Game = 0
                getCustomerProfile.PBR = 0
                
                ####################################
                getCustomerProfile.Animal = 0
                getCustomerProfile.Character = 0
                getCustomerProfile.Food = 0
                getCustomerProfile.Plant = 0
                getCustomerProfile.Weapon = 0
                getCustomerProfile.Vehicle = 0
                ####################################
                getCustomerProfile.TotalAnalysedProducts = 0

                db.session.commit()
            
            #A new user who does not provide interested product types
            else:
                newCustomerProfile = CustomerProfile(
                userID = current_user.id,
                Print = 0,
                Game = 0,
                PBR = 0,
                Animal = 0,
                Character = 0,
                Food = 0,
                Plant = 0,
                Weapon = 0,
                Vehicle = 0,
                TotalAnalysedProducts = 0)
            
                db.session.add(newCustomerProfile)
                db.session.commit() #Confirm and update

############### Content-Based Filtering ###############

def RecommendedProducts_ContentBased(PriorNumber, Numbers):
    
    #PriorNumber = get products according to user's profile highest type weight.
    #Numbers = get products by calcauting the sum of weights

    getCustomerProfile = CustomerProfile.query.filter_by(userID = current_user.id).first()

    CP1 = pd.DataFrame(columns=['3DPrint', 'Game', 'PBR'], index=["RatedWeight"])
    CP2 = pd.DataFrame(columns=['Animal', 'Character', 'Food', 'Plant', 'Weapon', 'Vehicle'], index=["RatedWeight"]) 
    
    CP1.loc["RatedWeight"] = [getCustomerProfile.Print, getCustomerProfile.Game, getCustomerProfile.PBR]

    CP2.loc["RatedWeight"] = [getCustomerProfile.Animal, getCustomerProfile.Character, getCustomerProfile.Food, 
                              getCustomerProfile.Plant, getCustomerProfile.Weapon, getCustomerProfile.Vehicle]
    
    CP1 = CP1.swapaxes("index", "columns")
    CP2 = CP2.swapaxes("index", "columns")

    CP1 = CP1.sort_values(by=['RatedWeight'], ascending=False)
    CP2 = CP2.sort_values(by=['RatedWeight'], ascending=False)

    CP = pd.concat([CP1, CP2], axis=0, join='inner')

    #Recommend Products based on user's profile and have bought something
    if(PurchaseHistory.query.filter_by(userID = current_user.id).first() is not None):
 
        RecommendProductsList = []

        PurchasedProductsList = PurchaseHistory.query.filter_by(userID = current_user.id).all()
        PurchasedProductsIDList = [] #Take the IDs of purchased products

        for x in PurchasedProductsList:
            PurchasedProductsIDList.append(x.productID)
        
        #Get the product whose type and subtype has the highest weight, and have not been purchased
        #Type -> [0]
        #Type -> [1]
        #Type -> [2]
        #Sub-Type -> [3]
        #limit(PriorNumber) = only return number of (PriorNumber)
        PrioritizedRecommendations = Products.query.filter(
            and_ (Products.productType == CP.iloc[0].name), (Products.productSubType == CP.iloc[3].name),
            (Products.productID.notin_(PurchasedProductsIDList))

            ).limit(PriorNumber).all()

        RecommendProductsList.extend(PrioritizedRecommendations)
        
        #If the # of prioitized recommeation products are lesser than inputted (PriorNumber)
        Numbers = PriorNumber - len(PrioritizedRecommendations) + Numbers

        #To find what type and subtype of product user purchased:
        purchasedType = np.array([])
        purchasedSubType = np.array([])
        if(CP.loc["3DPrint"]["RatedWeight"] > 0):
            purchasedType = np.append(purchasedType, "3DPrint")
        if(CP.loc["Game"]["RatedWeight"] > 0):
            purchasedType = np.append(purchasedType, "Game")
        if(CP.loc["PBR"]["RatedWeight"] > 0):
            purchasedType = np.append(purchasedType, "PBR")
            
        if(CP.loc["Animal"]["RatedWeight"] > 0):
            purchasedSubType = np.append(purchasedSubType, "Animal")
        if(CP.loc["Character"]["RatedWeight"] > 0):
            purchasedSubType = np.append(purchasedSubType, "Character")
        if(CP.loc["Food"]["RatedWeight"] > 0):
            purchasedSubType = np.append(purchasedSubType, "Food")
        if(CP.loc["Plant"]["RatedWeight"] > 0):
            purchasedSubType = np.append(purchasedSubType, "Plant")
        if(CP.loc["Weapon"]["RatedWeight"] > 0):
            purchasedSubType = np.append(purchasedSubType, "Weapon")
        if(CP.loc["Vehicle"]["RatedWeight"] > 0):
            purchasedSubType = np.append(purchasedSubType, "Vehicle")

        ProductsList = getProductListByTypeORSubType(purchasedType, purchasedSubType)

        #Calculate the weights of all products        
        ProductWeights = pd.DataFrame(columns=["ProductID", "ProductName", "Weight", "Type", "Sub-Type"])

        for PLists in ProductsList:

            newRow= [0,0,0, "", ""]

            #Dont include those are already purchased and inside the prior recommedation list
            if(PLists.productID not in PurchasedProductsIDList and PLists not in PrioritizedRecommendations):
                newRow[0] = PLists.productID
                newRow[1] = PLists.productName

                if("3DPrint" in PLists.productType):
                    newRow[2] = CP.loc["3DPrint"]["RatedWeight"]
                    newRow[3] = "3DPrint"
                elif("Game" in PLists.productType):
                    newRow[2] = CP.loc["Game"]["RatedWeight"]
                    newRow[3] = "Game"
                elif("PBR" in PLists.productType):
                    newRow[2] = CP.loc["PBR"]["RatedWeight"]
                    newRow[3] = "PBR"

                if("Animal" in PLists.productSubType):
                    newRow[2] += CP.loc["Animal"]["RatedWeight"]

                if("Character" in PLists.productSubType):
                    newRow[2] += CP.loc["Character"]["RatedWeight"]

                if("Food" in PLists.productSubType):
                    newRow[2] += CP.loc["Food"]["RatedWeight"]

                if("Plant" in PLists.productSubType):
                    newRow[2] += CP.loc["Plant"]["RatedWeight"]

                if("Weapon" in PLists.productSubType):
                    newRow[2] += CP.loc["Weapon"]["RatedWeight"]

                if("Vehicle" in PLists.productSubType):
                    newRow[2] += CP.loc["Vehicle"]["RatedWeight"]

                newRow[4] += PLists.productSubType

                ProductWeights.loc[PLists.productID] = newRow
        

        ProductWeights = ProductWeights.sort_values(by=['Weight'], ascending=False).reset_index(drop=True)
        #reset_index(drop=True) = reset the index, making the index starting from 0

        #lack of order (X)
        # TheOtherRecommendedProduct = Products.query.filter(Products.productID.in_(ProductWeights.head(Numbers).ProductID)).all()
        # RecommendProductsList.extend(TheOtherRecommendedProduct)

        #It has order (Most optimal to least)
        TopProducts = ProductWeights.head(Numbers)
        for x in range(Numbers):
            TheOtherRecommendedProduct = Products.query.filter(Products.productID == TopProducts.loc[x].ProductID).first()
            RecommendProductsList.append(TheOtherRecommendedProduct)
 
        #For demonstration purpose
        print("\n(Content-Based) Prioritized Recommendation:")
        for x in PrioritizedRecommendations:
            print(x.productID, ": ", x.productName)
        
        print("\n(Content-Based) Product Weight List:")
        print(ProductWeights)
        
        print("\n(Content-Based) Recommendation List:")
        print(RecommendProductsList)

        return RecommendProductsList

    #Recommend Products based on user's inputted interests if he/she has not bought anything yet
    elif(Users.query.filter_by(id = current_user.id).first().interestType !="" or Users.query.filter_by(id = current_user.id).first().interestSubType !=""):
        
        #To find what type and subtype of product user purchased:
        purchasedType = np.array([])
        purchasedSubType = np.array([])
        if(getCustomerProfile.Print > 0):
            purchasedType = np.append(purchasedType, "3DPrint")
        if(getCustomerProfile.Game > 0):
            purchasedType = np.append(purchasedType, "Game")
        if(getCustomerProfile.PBR > 0):
            purchasedType = np.append(purchasedType, "PBR")
            
        if(getCustomerProfile.Animal > 0):
            purchasedSubType = np.append(purchasedSubType, "Animal")
        if(getCustomerProfile.Character > 0):
            purchasedSubType = np.append(purchasedSubType, "Character")
        if(getCustomerProfile.Food > 0):
            purchasedSubType = np.append(purchasedSubType, "Food")
        if(getCustomerProfile.Plant > 0):
            purchasedSubType = np.append(purchasedSubType, "Plant")
        if(getCustomerProfile.Weapon > 0):
            purchasedSubType = np.append(purchasedSubType, "Weapon")
        if(getCustomerProfile.Vehicle > 0):
            purchasedSubType = np.append(purchasedSubType, "Vehicle")

        RecommendProductsList = getProductListByTypeORSubType(purchasedType, purchasedSubType)
        
        #Randomly pick products from list
        K_ = PriorNumber + Numbers
        if(len(RecommendProductsList) >= K_):  #Sometimes k value could be larger than the # of products inside RecommendProductsList
            RecommendProductsList = random.sample(RecommendProductsList, k = K_ )
        else:
            RecommendProductsList = random.sample(RecommendProductsList, k = len(RecommendProductsList) )

        return RecommendProductsList
    
    #Can't recommend anything if user does not tell anything.
    else:
        return ""
    
    """ Version 1: Merge types
        CP = createProfile()
        print(CP)

        TypeNameList = list(CP.index.values)

        ProductsCandidates = np.array([])

        #Getting all candidates 
        for X in TypeNameList:
                
            #X[0] = Type, X[1] = Sub-Types
            X = X.split('-', 1)
            X[1].replace("-", " ")

            ProductsCandidates = np.append(ProductsCandidates,
                            (Products.query.filter(and_(Products.productType == X[0] , Products.productSubType == X[1])).all()))



        #Numbers = how much product do I want to recommend
        print(ProductsCandidates[0:Numbers])
        """

############### User-based Collbrative Filtering ###############

#Instead of taking purchased item to calculate cosine similarities
#Mine uses customer profile to do that.
#So that unpopular products can be recommended to targeted user as well
#Unpopular products means a product that have not been purchased by many users.
#This can solve cold-start problem for products

#Step 1: Find K similar users with cosine similarities
#Step 2: Take the unpurchased products from similar users
#Step 3: Predicted rating of those products

def FindSimilarUser_CF():

    print("\n\n===============================\n")

    TargetedCustomerProfile = CustomerProfile.query.filter_by(userID = current_user.id).first()

    #If the customer profile is all 0
    if(TargetedCustomerProfile.Print == 0 and TargetedCustomerProfile.Game == 0 and TargetedCustomerProfile.PBR == 0 
       and TargetedCustomerProfile.Animal == 0 and TargetedCustomerProfile.Character == 0 and TargetedCustomerProfile.Food == 0 
       and TargetedCustomerProfile.Plant == 0 and TargetedCustomerProfile.Weapon == 0 and TargetedCustomerProfile.Vehicle == 0):
        
        return None

    else:

        ##Version 1, find similar users by cosine similarity
        """
        AllCustomerProfile = CustomerProfile.query.filter( (CustomerProfile.TotalAnalysedProducts > 0) | (CustomerProfile.userID == current_user.id) ).all() #Only pick users who have purchased at least one product
        
        if(len(AllCustomerProfile) == 1 ): return np.array([TargetedCustomerProfile]) #If there is no similar user, no need to continue the calculation, however, it also mean the database only have one user

        target_user_index = 0 #Initialize var

        # | User ID |
        # | Print | Game | PBR | 
        # | Animal | Character | Food | Plant | Weapon | Vehicle
        # = 9 column

        CustomerProfile_Matrix = np.zeros((len(AllCustomerProfile), 10))

        for x, profile in enumerate(AllCustomerProfile):
            
            CustomerProfile_Matrix[x, :] = profile.userID, profile.Print, profile.Game, profile.PBR, profile.Animal, profile.Character, profile.Food, profile.Plant, profile.Weapon, profile.Vehicle 

            #Remember the index of targeted user
            if(profile.userID == TargetedCustomerProfile.userID):
                target_user_index = x

        #Put targeted user in first row
        CustomerProfile_Matrix = np.roll(CustomerProfile_Matrix, -target_user_index, axis=0)

        #Remove the customer profile where all values(weights) are all zero.
        MatrixMask = np.all(CustomerProfile_Matrix[:, 1:] == 0, axis=1)
        CustomerProfile_Matrix = CustomerProfile_Matrix[~MatrixMask]

        CustomerProfile_Matrix_userID = np.array(CustomerProfile_Matrix[:, 0]) #The first one, arr[0], is the targeted user.
        CustomerProfile_Matrix = CustomerProfile_Matrix[:, 1:] #The first one, arr[0], is the targeted user.

        #Calcluate Cosine Similarity
        # !! First one (arr[0]) is targeted user himself.
        CosineSimilarityArray = np.zeros((0,2))
        for x, row in enumerate(CustomerProfile_Matrix):

            #(A.B) / (||A||.||B||)
            #A.B is dot product of A and B
            CosineSimilarity = [CustomerProfile_Matrix_userID[x], np.dot(CustomerProfile_Matrix[0], row)/(norm(CustomerProfile_Matrix[0])*norm(row))]

            CosineSimilarityArray = np.append(CosineSimilarityArray, [CosineSimilarity], axis=0)

        # Sort Cosine Similarity in descending order
        SortedCosineSimilarityArray = CosineSimilarityArray[CosineSimilarityArray[:, 1].argsort()[::-1]]
        
        print("Cosine Sim (uID, value): \n", CosineSimilarityArray)

        #Pick K similar users
        SimilarUsers = np.array([])
        for x, y in enumerate(SortedCosineSimilarityArray):

            if(x != 0): #Exclude targeted(first) user
                SimilarUser = Users.query.filter_by( id = y[0] ).first()
                SimilarUsers = np.append(SimilarUsers, [SimilarUser], axis=0)

            if(x == K):
                break

        print("\nTargeted User ID: %d" %CosineSimilarityArray[0][0])

        print("\nPicked Similar Users (K=%d)" % K, SimilarUsers)

        print("\n===============================")
    """
        
        ##Version 2, find similar users by KNN
        
        #Only pick users who have purchased at least one product and is not targeted user
        AllCustomerProfile = CustomerProfile.query.filter( and_(CustomerProfile.TotalAnalysedProducts > 0), (CustomerProfile.userID != current_user.id) ).all() 
        
        #If there is only one other user in database, we can save time from KNN
        if(len(AllCustomerProfile) == 1):  

            #Find the other user
            SimilarUsers = np.array([Users.query.filter_by( id = x.userID  ).first()])

            return SimilarUsers
        
        else:

            CustomerProfiles_Array = np.empty((0, 9)) #Array for weights

            TargetProfile_Array = np.array([TargetedCustomerProfile.Print, 
                                            TargetedCustomerProfile.Game, 
                                            TargetedCustomerProfile.PBR, 
                                            TargetedCustomerProfile.Animal, 
                                            TargetedCustomerProfile.Character, 
                                            TargetedCustomerProfile.Food, 
                                            TargetedCustomerProfile.Plant, 
                                            TargetedCustomerProfile.Weapon, 
                                            TargetedCustomerProfile.Vehicle])
            
            for profile in AllCustomerProfile:
                
                temp = np.array([profile.Print, profile.Game, profile.PBR, profile.Animal, profile.Character, profile.Food, profile.Plant, profile.Weapon, profile.Vehicle])
                CustomerProfiles_Array = np.append(CustomerProfiles_Array, [temp], axis = 0)

            if(len(CustomerProfiles_Array) == 2):  #If the database only contain 2 other user
                K = 2
            else:
                K = 3

            #kNN only accept 2D array as input, after that, it sort sub-array inside 2d array, and then only output the sorted indices of sub-array.
            #So, we will take the sorted indices to rearrange element inside "AllCustomerProfile"

            knnModel = NearestNeighbors(n_neighbors= K, algorithm='auto').fit(CustomerProfiles_Array)
            distance, sortedSimilarUsersIndex = knnModel.kneighbors(TargetProfile_Array.reshape(1, -1))

            #sortedSimilarUsersIndex will be the sorted indices of CustomerProfiles_Array, 
            # but it is 2D [[0 1 3]], so convert it back to 1d with .ravel() [0 1 3], 
            # after that it is not an array, use to_list() to make it contains elements [0, 1, 3]
            sortedSimilarUsersIndex = sortedSimilarUsersIndex.ravel().tolist()
            #print(sortedSimilarUsersIndex)
            
            #Get the similar users that are currently represented as customer profile.
            SimilarCustomerProfiles_Array = [AllCustomerProfile[i] for i in sortedSimilarUsersIndex]
            #print(SimilarCustomerProfiles_Array)

            #Pick user by customer profile
            SimilarUsers = np.array([])
            for x in SimilarCustomerProfiles_Array:

                SimilarUser = Users.query.filter_by( id = x.userID  ).first()
                SimilarUsers = np.append(SimilarUsers, [SimilarUser], axis=0)

            print("TargetUserID:", TargetedCustomerProfile.userID)

            print("\nKNN Result:")

            #For displaying results to terminal
            distance = distance.ravel().tolist() #[[0.1 0.6]] -> [0.1 0.6] -> [0.1, 0.6]
            for i, user in enumerate(SimilarUsers):
                print("Distance: %.4f" %distance[i], "\t User ID: %i" %user.id)

            print("\n===============================")

    return SimilarUsers

def RecommendProduct_CollaborativeFiltering(RecNum, lowestRating):

    SimilarUsers = FindSimilarUser_CF() #Note: The array does not contain targeted user.

    if(SimilarUsers is not None):
        
        if(len(SimilarUsers) == 0):
            return "Database only contains one user"

        i = 0
        Nestbreak = False
        RecommendUserProduct = []
        addedProducts = [] # keep track of added products to avoid duplication

        # Recommend products that are rated 5 to 4, from similar users
        for x in SimilarUsers:
            SelectedPurchasedProducts_Query = PurchaseHistory.query.filter(and_(PurchaseHistory.userID == x.id), (PurchaseHistory.productRating >= lowestRating) ).limit(RecNum).all()

            Temp = np.array([])
            Temp = np.append(Temp, [x], axis = 0)
            for queryProductHistory in SelectedPurchasedProducts_Query:

                # To check whether the targeted user has purchased the recommended product or not
                if( PurchaseHistory.query.filter( and_ (PurchaseHistory.productID == queryProductHistory.productID) , (PurchaseHistory.userID == current_user.id) ).first() is None):
                    product = Products.query.filter_by(productID = queryProductHistory.productID).first()

                    # Check if the product is already in the added_products list
                    if(product.productID not in addedProducts):
                        Temp = np.append(Temp, [queryProductHistory], axis = 0)
                        Temp = np.append(Temp, [product], axis = 0)

                        addedProducts.append(product.productID) # add the product ID to addedProducts
                        i += 1

                    if i == RecNum:
                        Nestbreak = True
                        break

            RecommendUserProduct.append(Temp.tolist())

            if Nestbreak:
                break

        # Output example: [[<Users 3>], [<Users 2>, <PurchaseHistory 3>, <Products 12>, <PurchaseHistory 4>, <Products 9>]]           
        return RecommendUserProduct
    
    else:
        return ""
    