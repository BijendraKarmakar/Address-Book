import models, requests, json
from fastapi import FastAPI, Depends
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import Address

app = FastAPI()


# This will create a database or table if not exist

models.Base.metadata.create_all(bind=engine)


# Using Pydantic for data validation, we just have to inherit this class and
# everytime pydantic will automatically validate the data for us

class AddressRequest(BaseModel):
    city: str
    latitude: float
    longitude: float


# This function will create a instance for session local and will handle the creation and
# closing of database session local 

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


# Get API to fetch all the addresses on the database

@app.get("/get_all_address")
def get_all_address(db: Session = Depends(get_db)):

    return db.query(Address).all()


# API to create new address we will use pydantic here for data validation 
# and will use get_db function for handling session local using dependency injection

@app.post("/add_address")
def add_address(address_request: AddressRequest, db: Session = Depends(get_db)):

    city = address_request.city
    latitude = address_request.latitude
    longitude = address_request.longitude


    #checking if both latitude and longitude provided by the user is valid
    # latitude should be in the range between -90 to 90 and longitude should be -180 to 180 

    if((-90 <= latitude <= 90) and (-180 <= longitude <= 180)):
        address = Address()
        address.city = city
        address.latitude = latitude
        address.longitude = longitude


        #Adding address model to the database

        db.add(address)
        db.commit()

        return {
            "msg": "New Address Added succesfully",
            "status": 100
        }
    
    else:
        return {
            "msg": "Invalid Coordinates, please check the coordinates and try again!",
            "status": 404
        }


# Update API to update existing data, using ID 

@app.put("/update_address")
def update_address(id: int, address_request: AddressRequest, db: Session = Depends(get_db)):


    # Checking if data is avaliable on database with the ID provided 

    data = db.query(Address).filter(Address.id == id).first()

    if data is None:
        return {
            "msg": "Invalid Address ID",
            "status": 404
        }
    
    city = address_request.city
    latitude = address_request.latitude
    longitude = address_request.longitude


    # Same validation for latitude and longtitude which we used on add_address API
    
    if((-90 <= latitude <= 90) and (-180 <= longitude <= 180)):
        data.city = city
        data.latitude = latitude
        data.longitude = longitude

        db.add(data)
        db.commit()

        return {
            "msg": "Updated succesfully",
            "status": 100
        }
    else:
        return {
            "msg": "Invalid Coordinates, please check the coordinates and try again!",
            "status": 404
        }
    

# Delete address API

@app.delete("/delete_address")
def delete_address(id: int, db: Session = Depends(get_db)):

    data = db.query(Address).filter(Address.id == id).first()

    if data is None:
        return {
            "msg": "Invalid Address ID",
            "status": 404
        }
    else:
        
        db.query(Address).filter(Address.id == id).delete()
        db.commit()

        return {
            "msg": "Deleted succesfully",
            "status": 100
        }


# API to fetch addresses within a particular range and provided latitude and longitude

@app.get("/get_address_within_range")
def get_address_within_range(range: int, latitude: float, longitude: float, db: Session = Depends(get_db)):

    api = "https://api.distancematrix.ai/maps/api/distancematrix/json?origins="
    api_key = "hLsi1OfeMrOPnTXCUx8xgd3PDPbLF4rYh7c9dl5WCZHFyplxqk6qMaTRakLkanf6"
    response = []


    # Latitude and longitude validation along with the range provided by the user 

    if((-90 <= latitude <= 90) and (-180 <= longitude <= 180) and range > 0):

        db_data = db.query(Address).all()

        for data in db_data:
            db_latitude = data.latitude
            db_longitude = data.longitude
            db_city = data.city


            # Using Distance matrix API to calculate the distance between two sets of latitude and longitude 

            api_response = api + str(latitude) + "," + str(longitude) + "&destinations=" + str(db_latitude) + "," + str(db_longitude) + "&key=" + api_key
            api_response = requests.get(api_response)
            json_data = json.loads(api_response.content)


            # Checking if the api request is succesfully and returing a list of all the addresses
            # which are within the range provided by user

            api_data = json_data['rows'][0]['elements'][0]

            if(json_data['status'] == "OK" and ('distance' in api_data) and (api_data['distance']['value']/1000) < range):
                data_to_append = {}
                data_to_append['city'] = db_city
                data_to_append['latitude'] = db_latitude
                data_to_append['longitude'] = db_longitude
                response.append(data_to_append)                

        return {
            "data": response,
            "status": 100
        }
    else:
        return {
            "msg": "Invalid Coordinates, please check the coordinates and try again!",
            "status": 404
        }
