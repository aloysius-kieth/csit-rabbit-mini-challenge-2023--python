from flask import Flask, jsonify, Response, json, request
from pymongo import MongoClient
from bson import ObjectId
from dateutil import parser
from datetime import date
from dataclasses import dataclass
import config

app = Flask(__name__)

@dataclass
class FilteredRecord:
    airline: str
    price: int

try:
    mongo = MongoClient(
        host=config.MONGO_URL,
        port=config.PORT)
    mongo.server_info()  # triggers exception if cannot connect to db

    db = mongo['minichallenge']
    # flightsCol = db['flights']
    # hotelsCol = db['hotels']
except Exception as e:
    print("Error connecting to db:" + e)


@app.route('/flight', methods=['GET'])
def GetCheapestFlight():
    args = request.args
    destination = args.get('destination')
    returnDate = args.get('returnDate')
    departureDate = args.get('departureDate')

    validQueries = True

    try:
        if (not destination):
            validQueries = False
        if (not returnDate or not date.fromisoformat(returnDate)):
            validQueries = False
        if (not departureDate or not date.fromisoformat(departureDate)):
            validQueries = False
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message: ": str(ex)}),
            status=400,
            mimetype="application/json"
        )
    if (not validQueries):
        return Response(
            response=json.dumps({"message: ": "Bad input"}),
            status=400,
            mimetype="application/json"
        )

    isoDepartureDate = parser.parse(departureDate)
    isoReturnDate = parser.parse(returnDate)

    departureQuery = {
        "srccity": {"$regex": "singapore", '$options': "i"},
        "destcity": {"$regex": destination, '$options': "i"},
        "date": {"$eq": isoDepartureDate},
    }

    returnQuery = {
        "srccity": {"$regex": destination, '$options': "i"},
        "destcity": {"$regex": "singapore", '$options': "i"},
        "date": {"$eq": isoReturnDate},
    }

    try:
        data = list(db.flights.find(departureQuery))
        for flight in data:
            flight["_id"] = str(flight["_id"])

        sortedDepartureFlights = sorted(data, key=lambda x: x['price'])

        resultDepartureFlights = []
        for i in sortedDepartureFlights:
            resultDepartureFlights.append(
                FilteredRecord(i['airline'], i['price']))
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message: ": "Cannot get flights!"}),
            status=500,
            mimetype="application/json"
        )
    else:
        try:
            data = list(db.flights.find(returnQuery))
            for flight in data:
                flight["_id"] = str(flight["_id"])

            sortedReturnFlights = sorted(data, key=lambda x: x['price'])

            resultReturnFlights = []
            for i in sortedReturnFlights:
                resultReturnFlights.append(
                    FilteredRecord(i['airline'], i['price']))

            result = []

            for i in range(len(resultReturnFlights)):
                resD = resultDepartureFlights[i]
                resR = resultReturnFlights[i]
                result.append({"City": destination,
                               "Departure Date": departureDate,
                               "Departure Airline": resD.airline,
                               "Departure Price": resD.price,
                               "Return Date": returnDate,
                               "Return Airline": resR.airline,
                               "Return Price": resR.price})

            return Response(
                response=json.dumps(result),
                status=200,
                mimetype="application/json"
            )
        except Exception as ex:
            print(ex)
            return Response(
                response=json.dumps({"message: ": ex}),
                status=400,
                mimetype="application/json"
            )


@app.route("/hotel", methods=['GET'])
def GetCheapestHotels():
    args = request.args
    checkInDate = args.get('checkInDate')
    checkOutDate = args.get('checkOutDate')
    destination = args.get('destination')

    validQueries = True

    try:
        if (not destination):
            validQueries = False
        if (not checkInDate or not date.fromisoformat(checkInDate)):
            validQueries = False
        if (not checkOutDate or not date.fromisoformat(checkOutDate)):
            validQueries = False

            isoCheckInDate = parser.parse(checkInDate)
            isoCheckOutDate = parser.parse(checkOutDate)
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message: ": str(ex)}),
            status=400,
            mimetype="application/json"
        )
    if (not validQueries):
        return Response(
            response=json.dumps({"message: ": "Bad input"}),
            status=400,
            mimetype="application/json"
        )

    isoCheckInDate = parser.parse(checkInDate)
    isoCheckOutDate = parser.parse(checkOutDate)

    query = {
        "city": {
            "$regex": destination,
            "$options": "i"
        },
        "date": {
            "$gte": isoCheckInDate,
            "$lte": isoCheckOutDate
        }
    }

    try:
        data = list(db.hotels.find(query))
        for hotel in data:
            hotel["_id"] = str(hotel["_id"])

        uniqueHotelNames = list({(hotel['hotelName']) for hotel in data})

        filteredUniqueResult = []

        for uniqueHotel in uniqueHotelNames:
            filteredHotels = [hotel for hotel in data if hotel['hotelName'] == uniqueHotel]
            total_price = sum(hotel['price'] for hotel in filteredHotels)
            filteredUniqueResult.append({'Hotel': uniqueHotel, 'Price': total_price})

        filteredUniqueResult = sorted(filteredUniqueResult, key=lambda x: x['Price'])

        result = []
        for i in range(len(filteredUniqueResult)):
            hotel = filteredUniqueResult[i]
            result.append({
                "City": destination,
                "Check In Date": checkInDate,
                "Check Out Date": checkOutDate,
                "Hotel": hotel["Hotel"],
                "Price": hotel["Price"]
            })
        
        print(result)
        
        return Response(
            response=json.dumps(result),
            status=200,
            mimetype="application/json"
        )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message: ": "Cannot get hotels!"}),
            status=500,
            mimetype="application/json"
        )


if __name__ == '__main__':
    app.run(port=config.PORT, debug=True)
