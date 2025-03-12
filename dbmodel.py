from app import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    userName = db.Column(db.String(255), unique=True)
    age = db.Column(db.Integer, unique=True)
    gender = db.Column(db.String(1), unique=True) #M/F
    
    interestType = db.Column(db.String(255))
    interestSubType = db.Column(db.String(255))
    totalPurchasedModels = db.Column(db.Integer)

    purchasedModels = db.relationship('PurchaseHistory')
    uploadedModels = db.relationship('Products')
    
class Products(db.Model):
    productID = db.Column(db.Integer, primary_key = True)
    productName = db.Column(db.String(255))
    productType = db.Column(db.String(255))
    productSubType = db.Column(db.String(255))
    productPrice = db.Column(db.Numeric(7,2))

    productUploadTime = db.Column(db.DateTime(timezone=True), default=func.now())
    uploaderID = db.Column(db.Integer, db.ForeignKey('users.id'))

    totalSales = db.Column(db.Integer)
    
class PurchaseHistory(db.Model):
    purchaseHistoryID = db.Column(db.Integer, primary_key = True)
    userID = db.Column(db.Integer, db.ForeignKey('users.id'))
    productID = db.Column(db.Integer, db.ForeignKey('products.productID'))
    purchaseTime = db.Column(db.DateTime(timezone=True), default=func.now())
    productRating = db.Column(db.Integer)

class CustomerProfile(db.Model):
    customerProfileID = db.Column(db.Integer, primary_key = True)
    userID = db.Column(db.Integer, db.ForeignKey('users.id'))

    Print = db.Column(db.Float)
    Game = db.Column(db.Float)
    PBR = db.Column(db.Float)
    Animal = db.Column(db.Float)
    Character = db.Column(db.Float)
    Food = db.Column(db.Float)
    Plant = db.Column(db.Float)
    Weapon = db.Column(db.Float)
    Vehicle = db.Column(db.Float)

    TotalAnalysedProducts = db.Column(db.Integer)