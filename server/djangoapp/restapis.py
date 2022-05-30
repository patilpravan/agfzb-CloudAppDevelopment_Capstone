import requests
import json
# import related models here
from requests.auth import HTTPBasicAuth
from .models import CarDealer, DealerReview

# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))

def get_request(url, api_key=False, **kwargs):
    print("inside get_request")
    print("kwargs:Prava ", kwargs)
    print(f"GET from {url}")
    if api_key:
        # Basic authentication GET
        try:
            response = requests.get(url, headers={'Content-Type': 'application/json'},
                                    params=kwargs, auth=HTTPBasicAuth('apikey', api_key))
        except:
            print("An error occurred while making GET request. ")
    else:
        # No authentication GET
        try:
            response = requests.get(url, headers={'Content-Type': 'application/json'},
                                    params=kwargs)
        except:
            print("An error occurred while making GET request. ")

    # Retrieving the response status code and content
    status_code = response.status_code
    print(f"With status {status_code}")
    json_data = json.loads(response.text)

    return json_data

# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)
def post_request(url, json_payload, **kwargs):
    json_obj = json_payload
    print("Payload: ", json_obj, ". Params: ", kwargs)
    print("POST to {} ".format(url))
    # print(json_payload["review"])
    try:
        response = requests.post(
            url, headers={'Content-Type': 'application/json'}, json=json_obj, params=kwargs)
    except:
        print("Network exception occurred")

    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    print(json_data)

# Create a get_dealers_from_cf method to get dealers from a cloud function
# def get_dealers_from_cf(url, **kwargs):
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list
def get_dealers_from_cf(url, **kwargs):
    print("inside get_dealers_from_cf")
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url)
    if json_result:
        # Get the row list in JSON as dealers
        dealerdict= json_result["body"]
        dealers=[]
        for item in dealerdict:
            dealers.append(item["doc"])
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"], id=dealer["id"], lat=dealer["lat"], long=dealer["long"], short_name=dealer["short_name"], st=dealer["st"], state=dealer["state"], zip=dealer["zip"])
            results.append(dealer_obj)

    return results

# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
# def get_dealer_by_id_from_cf(url, dealerId):
# - Call get_request() with specified arguments
# - Parse JSON results into a DealerView object list
def get_dealers_by_state(url, state):
    print("inside get_dealers_from_cf")
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url, state=state)
    if json_result:
        # Get the row list in JSON as dealers
        dealerdict= json_result["body"]
        dealers=[]
        for item in dealerdict:
            dealers.append(item["doc"])
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"], id=dealer["id"], lat=dealer["lat"], long=dealer["long"], short_name=dealer["short_name"], st=dealer["st"], state=dealer["state"], zip=dealer["zip"])
            results.append(dealer_obj)

    return results


def get_dealer_reviews_from_cf(url, dealer_id):
    results = []
    print("pravan32d:", dealer_id,"url: ",url)
    # Perform a GET request with the specified dealer id
    json_result = get_request(url, dealerId=dealer_id)
    print("pravan32 :",json_result)
    if json_result:
        # Get all review data from the response
        reviews = json_result["body"]["data"]["docs"]
        # For every review in the response   
        for review in reviews:
            # Create a DealerReview object from the data
            # These values must be present
            review_content = review["review"]
            id = review["id"]
            name = review["name"]
            purchase = review["purchase"]
            dealership = review["dealership"]

            try:
                # These values may be missing
                car_make = review["car_make"]
                car_model = review["car_model"]
                car_year = review["car_year"]
                purchase_date = review["purchase_date"]

                # Creating a review object
                review_obj = DealerReview(dealership=dealership, id=id, name=name,
                                          purchase=purchase, review=review_content, car_make=car_make,
                                          car_model=car_model, car_year=car_year, purchase_date=purchase_date
                                          )

            except KeyError:
                print("Something is missing from this review. Using default values.")
                # Creating a review object with some default values
                review_obj = DealerReview(
                    dealership=dealership, id=id, name=name, purchase=purchase, review=review_content)

            # Analysing the sentiment of the review object's review text and saving it to the object attribute "sentiment"
            review_obj.sentiment = analyze_review_sentiments(review_obj.review)
            print(f"sentiment: {review_obj.sentiment}")

            # Saving the review object to the list of results
            results.append(review_obj)

    return results

# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# def analyze_review_sentiments(text):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative
def analyze_review_sentiments(review):
    api_key = "9c6MgdyqFNXXxMSVDnXQHwayUxyPgronOPR2uAJpgxPT"
    url = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/1733dd8b-f1ee-45e4-8cc4-4322fff19e07"
    text = review
    version = '2020-08-01'
    authenticator = IAMAuthenticator(api_key)
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        version=version,
        authenticator=authenticator
    )
    natural_language_understanding.set_service_url(url)
    try:
        response = natural_language_understanding.analyze(text=text, features=Features(
            sentiment=SentimentOptions())).get_result()
        print(json.dumps(response))
        # sentiment_score = str(response["sentiment"]["document"]["score"])
        sentiment_label = response["sentiment"]["document"]["label"]
    except:
        print("Review is too short for sentiment analysis. Assigning default sentiment value 'neutral' instead")
        sentiment_label = "neutral"
    # print(sentiment_score)
    # print(sentiment_label)
    sentimentresult = sentiment_label

    return sentimentresult


