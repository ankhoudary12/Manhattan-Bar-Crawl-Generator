import flask
import pandas as pd

bars_df=pd.read_pickle('bars_df.pickle')
sims_df=pd.read_pickle('sims_df.pickle')

def return_bars(bar, d=1, number=10):

    '''Will ultimately take a bar, radius, and number (n) and return closest (n) bars in radius (d)  in terms of
    vibe/type  to iniitial bar'''

    def find_nearest_bars(bar, d=1 ,number=10):
        from math import radians, cos, sin, asin, sqrt
        import pandas as pd

        def haversine(lon1, lat1, lon2, lat2):
            """
            Calculate the great circle distance between two points
            on the earth (specified in decimal degrees)
            """
            # convert decimal degrees to radians
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

            # haversine formula
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 3956 # For miles
            return c * r

        def is_in_area(center_lon, center_lat, test_lon, test_lat, radius = 1):
            '''Will determine if lat,lng is within radius of desired point'''
            a = haversine(center_lon, center_lat, test_lon, test_lat)
            if a <= radius:
                return True
            return False


        import jellyfish

        def get_closest_match(x, list_strings):

            '''Will return string that best matches list of strings according to jaro winkler score'''

            best_score= 0
            best_match=None

            for title in list_strings:

                current_score=jellyfish.jaro_winkler(x, title)

                if current_score > best_score:
                    best_score = current_score
                    best_match = title

            if best_score > 0.75:
                return best_match

            else:
                return None


        bar = get_closest_match(bar, bars_df.index)

        bool_array=[]



        if d < 1:
            d=1

        for i in bars_df['coordinates']: # make a boolean array of whether bars are within radius of desired bar

            try:
                bool_array.append(is_in_area(bars_df[bars_df.index==bar]['coordinates'][0][0]\
                                             ,bars_df[bars_df.index==bar]['coordinates'][0][1],\
                                             i[0],i[1], radius=d))

            except:
                bool_array.append(None)

        bool_dict=dict(zip(bars_df.index,bool_array)) # create dict of bar name:True/False whether in desired radius

        bool_df=pd.Series(bool_dict).to_frame()

        matching_bars=sims_df.join(bool_df[bool_df[0]==True], how='inner') #dataframe containing only bars within radius

        final_bars=bars_df.join(matching_bars[bar].sort_values(ascending=False)[0:number+1], how='right')

        return final_bars.sort_values(by=bar, ascending=False) #returns list of bars by closest cosine similarity


    def pack_bars(df):
        '''Will take resuls of finding nearest bars and return a list of bar dictionaries containing relevant info'''

        import operator

        bars=[]

        for index, row in df.iterrows():
            a=row.index
            a={}
            a['name']=row['name']
            a['neighborhood']=row['neighborhood']
            a['price']=row['price']
            a['lat']=row['coordinates'][0]
            a['lng']=row['coordinates'][1]
            a['url']=row['url']
            bars.append(a)

        bars.sort(key=operator.itemgetter('lat')) #arrange bars by longitude coordinate

        return bars


    return pack_bars(find_nearest_bars(bar, d, number))

#---------- URLS AND WEB PAGES -------------#

# Initialize the app
application = flask.Flask(__name__)

# Homepage
@application.route("/")
def viz_page():
    """
    Homepage: serve our visualization page, awesome.html
    """
    with open("index.html", 'r') as viz_file:
        return viz_file.read()

@application.route("/recommend", methods=["POST"])
def score():
    """
    When A POST request with json data is made to this uri,
    Read the example from the json, get similar bars, and
    send it with a response
    """

    # Get decision score for our example that came with the request
    data = flask.request.json
    print(data)
    x = data["example"][0]
    radius=int(data["example"][1])
    number=int(data["example"][2])
    print(x)
    bars = return_bars(x,radius,number)
    print(bars)
    # Put the result in a nice dict so we can send it as json
    results = {"score": bars}
    return flask.jsonify(results)


# Start the app server on port 80
# (The default website port)
if __name__ == "__main__":
  application.run()
# application.run(host='0.0.0.0')
# application.run(debug=True)
